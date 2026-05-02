from pydantic import BaseModel, EmailStr
from typing import Optional,Generic, TypeVar

# Define a generic type variable
T = TypeVar("T")

class ResponseSchema(BaseModel, Generic[T]):
    data: Optional[T]
    message: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "candidate"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Data(BaseModel):
    name: Optional[str]=None
    email: Optional[str]=None
    access_token: Optional[str]=None
    refresh_token: Optional[str]=None
    email_verified:Optional[bool]=None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserEmailSchema(BaseModel):
    email: EmailStr

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

class NewPassword(BaseModel):
    new_password: str
    class Config:
        arbitrary_types_allowed = True

class ProfileUpdate(BaseModel):
    username: Optional[str] = None

class UserDataResponse(BaseModel):
    id: str
    email: str
    role: str
    username: str
    scans_remaining: int

class ProfileResponse(BaseModel):
    message: str
    user_data: UserDataResponse

    