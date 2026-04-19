from sqlmodel import Session, select
from db.models.user import User
from schemas.user import UserCreate, UserLogin, OTPVerification, UserEmailSchema, Data, ResponseSchema
from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
import smtplib
import random
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Passlib to use bcrypt for secure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_otp():
    return str(random.randint(100000, 999999))

# ==========================================
# READ OPERATIONS (SQLModel Syntax)
# ==========================================
def fetch_user_by_email(db: Session, email: str):
    stmt = select(User).where(User.email == email)
    return db.exec(stmt).first()

def fetch_user_by_id(db: Session, user_id: uuid.UUID):
    stmt = select(User).where(User.id == user_id)
    return db.exec(stmt).first()

def get_user_details(db: Session, user_id: uuid.UUID):
    db_user = fetch_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    data = Data(name=db_user.username, email=db_user.email)
    return ResponseSchema[Data](data=data, message="User found successfully")

# ==========================================
# CREATE OPERATION (Signup)
# ==========================================
def create_user(db: Session, user: UserCreate): 
    existing_user = fetch_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    if user.role not in ["candidate", "employer"]:
        raise HTTPException(status_code=400, detail="Invalid role. Choose either 'candidate' or 'employer'.")

    hashed_password = hash_password(user.password)
    otp = generate_otp()
    
    # Map Schema to SQLModel
    db_user = User(
        username=user.name, 
        email=user.email, 
        password=hashed_password,
        role=user.role,
        otp=otp,
        email_verification=False,
        otp_created_at=datetime.now(timezone.utc)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send OTP to user's email 
    send_otp_to_email(db_user.email, db_user.otp)
    
    data = Data(name=user.name, email=user.email, email_verified=db_user.email_verification)
    return ResponseSchema[Data](data=data, message="User created successfully. Please verify the OTP sent to your email.")

# ==========================================
# UPDATE OPERATIONS (Login, OTP, Password)
# ==========================================
def login_user(db: Session, user_login: UserLogin):
    user = fetch_user_by_email(db, user_login.email)
    if user is None or not verify_password(user_login.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    if user.email_verification is False:
        user.otp = generate_otp()
        user.otp_created_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        send_otp_to_email(user.email, user.otp)
        data = Data(name=user.username, email=user.email, email_verified=user.email_verification)
        return ResponseSchema[Data](data=data, message="Email not verified. A new OTP has been sent to your email.")
    
    # Note: We will build create_access_token next!
    from db.repository.jwt import create_access_token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}, 
        expires_delta=timedelta(minutes=30)
    )
    
    data = Data(name=user.username, email=user.email, access_token=access_token)
    return ResponseSchema[Data](data=data, message="Login successful")

def verify_otp(db: Session, user: OTPVerification):
    db_user = fetch_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    if db_user.otp is None:
        raise HTTPException(status_code=404, detail="OTP not found")

    # Ensure timezone awareness matches
    otp_expires_time = db_user.otp_created_at.replace(tzinfo=timezone.utc) + timedelta(minutes=5)
    if datetime.now(timezone.utc) > otp_expires_time:
        db_user.otp = None
        db.commit()
        raise HTTPException(status_code=410, detail="OTP has expired. Please request a new one.")
    
    if db_user.otp != user.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    
    db_user.email_verification = True
    db_user.otp = None
    db.commit() 
    db.refresh(db_user)
    
    from db.repository.jwt import create_access_token
    token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email}, 
        expires_delta=timedelta(minutes=30)
    ) 
    
    data = Data(name=db_user.username, email=db_user.email, access_token=token)
    return ResponseSchema[Data](data=data, message="OTP verification completed successfully.")

def reset_password(db: Session, user: UserEmailSchema):
    db_user = fetch_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    otp = generate_otp()
    db_user.otp = otp
    db_user.otp_created_at = datetime.now(timezone.utc)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    send_otp_to_email(user.email, otp)
    data = Data(email=db_user.email)
    return ResponseSchema[Data](data=data, message="OTP has been sent to your email.")

def update_password(db: Session, user: UserLogin):
    db_user = fetch_user_by_email(db, user.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if db_user.otp is not None:
        raise HTTPException(status_code=400, detail="OTP not verified. Please verify your OTP.")
        
    db_user.password = hash_password(user.password)  
    db.commit()
    db.refresh(db_user)

    data = Data(name=db_user.username, email=db_user.email)
    return ResponseSchema[Data](data=data, message="Password reset successfully.")

# ==========================================
# DELETE OPERATION
# ==========================================
def delete_user_by_id(db: Session, user_id: uuid.UUID):
    db_user = fetch_user_by_id(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

# ==========================================
# UTILITY: EMAIL SENDER
# ==========================================
def send_otp_to_email(email: str, otp: str):
    # Pro Tip: Pull these from .env so you don't push passwords to GitHub!
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD") 
    mail_from = mail_username
    mail_server = "smtp.gmail.com"
    mail_port = 587 

    message = MIMEText(f"Your SkillBridge AI OTP is: {otp}")
    message["From"] = mail_from
    message["To"] = email
    message["Subject"] = "SkillBridge AI - OTP Verification"

    try:
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls() 
            server.login(mail_username, mail_password) 
            server.sendmail(mail_from, email, message.as_string()) 
    except Exception as e:
        print(f"Failed to send email: {e}")