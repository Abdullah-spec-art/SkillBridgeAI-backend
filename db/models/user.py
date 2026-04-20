from sqlmodel import Field, Relationship
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from .tablemodel import TableModel

if TYPE_CHECKING:
    from .analysis import Analysis 

class User(TableModel, table=True):
    __tablename__ = 'users'
    
    username: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True, index=True)
    password: str = Field(nullable=False)
    role: str = Field(nullable=False, max_length=10, index=True, default="user")
    
    # SkillBridge Specific Field
    skill_level: Optional[str] = Field(default=None)
    
    # OTP & Verification
    otp: Optional[str] = Field(default=None)
    otp_created_at: Optional[datetime] = Field(default=None)
    email_verification: bool = Field(default=False)



    analyses: List["Analysis"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )