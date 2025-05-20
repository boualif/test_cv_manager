from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.database.postgresql import Base

class AnalysisCache(Base):
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    candidate_id = Column(Integer, nullable=False)
    job_title = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    analysis_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Contrainte d'unicité pour job_id et candidate_id
    __table_args__ = (
        UniqueConstraint('job_id', 'candidate_id', name='uix_job_candidate'),
        # Index pour accélérer les recherches
        Index('idx_job_candidate', 'job_id', 'candidate_id'),
    )