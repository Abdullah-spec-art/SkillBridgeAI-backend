from fastapi import APIRouter, Depends, HTTPException, Response, Request
from jose import JWTError
from sqlmodel import Session 
from sqlmodel import Session
import uuid
from pydantic import BaseModel
# Import our database session generator
from db.database import get_session
from core.config import settings
# Import the repository logic we just wrote
from db.models.analysis import Analysis
from db.repository import user as user_repo
from db.repository import jwt
from db.repository.jwt import create_refresh_token, get_current_user,create_access_token
from sqlmodel import func
# Import our schemas for validation
from schemas.google_auth import GoogleAuthRequest
from schemas.user import (
    ProfileResponse,
    ProfileUpdate,
    UserCreate, 
    UserLogin, 
    ResponseSchema, 
    OTPVerification, 
    UserEmailSchema,
    RefreshTokenRequest
)

# Import the Database model for type hinting
from db.models.user import User

# Set up the router
router = APIRouter(prefix="/auth", tags=["Authentication"])

def set_auth_cookies(response: Response, access_token: str, refresh_token: str = None):
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, 
        secure=True, 
        samesite="none",
        max_age=30*60,
        path="/"
    )
    if refresh_token:
        response.set_cookie(
            key="refresh_token", 
            value=refresh_token, 
            httponly=True, 
            secure=True, 
            samesite="none",
            max_age=7*24*60*60,
            path="/"
        )
    response.set_cookie(
        key="is_logged_in", 
        value="true", 
        httponly=False, 
        secure=True, 
        samesite="none",
        max_age=30*60,
        path="/"
    )

@router.post("/signup", response_model=ResponseSchema)
def signup(user: UserCreate, db: Session = Depends(get_session)):
    return user_repo.create_user(db=db, user=user)

@router.post("/login", response_model=ResponseSchema)
def login(user_login: UserLogin, response: Response, db: Session = Depends(get_session)):
    result = user_repo.login_user(db=db, user_login=user_login)
    if result.data and result.data.access_token:
        set_auth_cookies(response, result.data.access_token, result.data.refresh_token)
    return result

@router.post("/verify-otp", response_model=ResponseSchema)
def otp_verification(user: OTPVerification, response: Response, db: Session = Depends(get_session)):
    result = user_repo.verify_otp(db=db, user=user)
    if result.data and result.data.access_token:
        set_auth_cookies(response, result.data.access_token, result.data.refresh_token)
    return result

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
def read_users_me(current_user: User = Depends(get_current_user),db: Session=Depends(get_session)):
    stats = user_repo.get_user_scan_stats(db, current_user.id)
    return {
        "message": "Token is valid! You have access to protected routes.",
        "user_data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
            "username": current_user.username, 
            "scans_remaining": current_user.scans_remaining,
            "total_analyses": stats["total_analyses"],
            "average_score": stats["average_score"]
        }
    }


@router.post("/google")
def google_auth(request: GoogleAuthRequest, response: Response, db: Session = Depends(get_session)):
    try:
        user = user_repo.UserRepository.authenticate_google_user(
            session=db, 
            google_token=request.google_token
        )
        
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})
        
        set_auth_cookies(response, access_token, refresh_token)
        
        return {
            "message": "Successfully logged in with Google",
            "user_data": {
                "id": str(user.id),
                "email": user.email,
                "name": user.username
            }
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        import traceback          # <-- Add this
        traceback.print_exc()     # <-- Add this: It forces the terminal to print the red traceback
        raise HTTPException(status_code=500, detail=f"Google authentication failed: {str(e)}")
    

@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        email = payload.get("email")
        sub = payload.get("sub")

        new_access_token = create_access_token(data={"email": email, "sub": sub})

        set_auth_cookies(response, new_access_token, refresh_token)

        return {"message": "Token refreshed successfully"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", secure=True, samesite="none", path="/")
    response.delete_cookie("refresh_token", secure=True, samesite="none", path="/")
    response.delete_cookie("is_logged_in", secure=True, samesite="none", path="/")
    return {"message": "Logged out successfully"}


@router.put("/me/profile", response_model=ProfileResponse)
def update_profile_route(
    profile_data: ProfileUpdate, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # 1. Pass the Pydantic data directly to your combined repository function
    updated_user = user_repo.update_user_profile(session, current_user, profile_data)
    
    # 2. Return the strict Pydantic response for React
    return {
        "message": "Profile updated successfully",
        "user_data": {
            "id": str(updated_user.id),
            "email": updated_user.email,
            "role": updated_user.role,
            "username": updated_user.username,
            "scans_remaining": updated_user.scans_remaining
        }
    }