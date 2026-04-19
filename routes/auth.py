from fastapi import APIRouter, Depends
from sqlmodel import Session
import uuid

# Import our database session generator
from db.database import get_session

# Import the repository logic we just wrote
from db.repository import user as user_repo
from db.repository.jwt import get_current_user

# Import our schemas for validation
from schemas.user import (
    UserCreate, 
    UserLogin, 
    ResponseSchema, 
    OTPVerification, 
    UserEmailSchema
)

# Import the Database model for type hinting
from db.models.user import User

# Set up the router
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=ResponseSchema)
def signup(user: UserCreate, db: Session = Depends(get_session)):
    return user_repo.create_user(db=db, user=user)

@router.post("/login", response_model=ResponseSchema)
def login(user_login: UserLogin, db: Session = Depends(get_session)):
    return user_repo.login_user(db=db, user_login=user_login)

@router.post("/verify-otp", response_model=ResponseSchema)
def otp_verification(user: OTPVerification, db: Session = Depends(get_session)):
    return user_repo.verify_otp(db=db, user=user)

@router.post("/forgot-password", response_model=ResponseSchema)
def forget_password(user: UserEmailSchema, db: Session = Depends(get_session)):
    return user_repo.reset_password(db=db, user=user)

@router.post("/new-password", response_model=ResponseSchema)
def new_password(user: UserLogin, db: Session = Depends(get_session)):
    return user_repo.update_password(db=db, user=user)

@router.get("/{user_id}", response_model=ResponseSchema)
def get_user_by_id(user_id: uuid.UUID, db: Session = Depends(get_session)):
    return user_repo.get_user_details(db=db, user_id=user_id)

@router.delete("/{user_id}")
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_session)):
    return user_repo.delete_user_by_id(db=db, user_id=user_id)

# ==========================================
# TEST ROUTE: Verify your JWT Token Works!
# ==========================================
@router.get("/me/profile", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    If you pass a valid token in the headers, this returns your user data.
    If the token is missing or expired, it throws a 401 Unauthorized.
    """
    return {
        "message": "Token is valid! You have access to protected routes.",
        "user_data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role
        }
    }