from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobBase(BaseModel):
    title: str = Field(..., description="Titre du poste")
    description: str = Field(..., description="Description détaillée du poste")
    competence_phare: Optional[str] = Field(None, description="Compétence principale requise")
    job_type_etiquette: str = Field("technique", description="Type du poste (technique, fonctionnel, technico-fonctionnel)")

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    competence_phare: Optional[str] = None
    job_type_etiquette: Optional[str] = None

class JobInDB(JobBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class JobResponse(JobInDB):
    created_by: Optional[str] = None

class MatchedCandidate(BaseModel):
    id: int
    name: str
    score: float
    match_quality: Optional[str] = None

    class Config:
        from_attributes = True

class CandidateMatchResponse(BaseModel):
    job_id: int
    matched_candidates: List[MatchedCandidate]
    
    class Config:
        from_attributes = True

# Fix this schema to be consistent with your endpoint
class CandidateMatchRequest(BaseModel):
    job_id: int = Field(..., description="ID du poste à analyser")
    candidates: List[int] = Field(..., description="Liste des IDs des candidats à analyser")
    min_score: Optional[float] = Field(0.0, description="Score minimum pour filtrer les résultats")
    limit: Optional[int] = Field(10, description="Nombre maximum de résultats à retourner")

    class Config:
        from_attributes = True