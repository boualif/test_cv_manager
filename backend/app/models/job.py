from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgresql import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    competence_phare = Column(String, nullable=True)
    job_type_etiquette = Column(String, nullable=False, default="technique")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship back to User
    #created_by = relationship("User")  # Supprimez back_populates="created_jobs"
    created_by = relationship("User", back_populates="created_jobs")


    def __repr__(self):
        return f"<Job {self.id}: {self.title} ({self.job_type_etiquette})>"