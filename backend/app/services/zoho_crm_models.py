from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CandidateData(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    skills: Optional[List[str]] = []
    current_position: Optional[str] = None
    cv_url: Optional[str] = None
    match_score: Optional[float] = None
    analysis_summary: Optional[str] = None

class JobData(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: Optional[str] = None
    salary_range: Optional[str] = None
    department: Optional[str] = None
    job_id: str

# Note: ZohoCRMSync class is temporarily disabled to avoid import issues
# It will be re-enabled once the basic authentication is working
