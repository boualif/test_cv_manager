# app/schemas/user.py
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator

class UserRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    SALES = "sales"
    HR = "hr"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "recruiter"
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["admin", "recruiter", "sales", "hr"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)  # Consistent 6-char minimum

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)  # Optional for updates
    
    @validator('role')
    def validate_optional_role(cls, v):
        if v is not None:
            valid_roles = ["admin", "recruiter", "sales", "hr"]
            if v not in valid_roles:
                raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Updated from orm_mode=True

# Define User schema as alias of UserInDB
class User(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str

class TokenData(BaseModel):
    sub: str  # username
    role: str  # Using string to match with the JWT payload
    exp: int  # Changed to int as JWT uses Unix timestamp
    
class UserActivityBase(BaseModel):
    activity_type: str
    description: Optional[str] = None

class UserActivityCreate(UserActivityBase):
    user_id: int

class UserActivity(UserActivityBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # Updated from orm_mode=True