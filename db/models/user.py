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
    password: Optional[str] = Field(nullable=True)
    auth_provider: str = Field(default="email") # "local" or "google"
    role: str = Field(nullable=False, max_length=10, index=True, default="candidate") 
    
    # SkillBridge Specific Field
    skill_level: Optional[str] = Field(default=None)
    
    # OTP & Verification
    otp: Optional[str] = Field(default=None)
    otp_created_at: Optional[datetime] = Field(default=None)
    email_verification: bool = Field(default=False)

    # for scans
    scans_remaining: int = Field(default=3)
    last_replenished_at: Optional[datetime] = Field(default=None)



    analyses: List["Analysis"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )