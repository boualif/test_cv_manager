# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.postgresql import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    SALES = "sales"
    HR = "hr"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    # Use String type for consistency instead of ENUM
    role = Column(String(20), nullable=False, default='recruiter')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Define relationship to UserActivity
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    
    # Fix: Add these relationships inside the User class
    added_candidates = relationship("Candidate", back_populates="added_by")
    created_jobs = relationship("Job", back_populates="created_by")
    

    
    # Properties for role checking (only one set, no duplicates)
    @property
    def is_admin(self):
        return self.role == "admin"
        
    @property
    def is_recruiter(self):
        return self.role == "recruiter"
        
    @property
    def is_sales(self):
        return self.role == "sales"
        
    @property
    def is_hr(self):
        return self.role == "hr"

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, upload_cv, view_profile, etc.
    description = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to User
    user = relationship("User", back_populates="activities")