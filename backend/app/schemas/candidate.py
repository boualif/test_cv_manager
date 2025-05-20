from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Schema for phone number information (used for CV parsing)
class PhoneNumberSchema(BaseModel):
    Number: Optional[str] = ""
    ISDCode: Optional[str] = ""
    OriginalNumber: Optional[str] = ""
    FormattedNumber: Optional[str] = ""
    Type: Optional[str] = ""
    Location: Optional[str] = ""

# Schema for degree information (used for CV parsing)
class DegreeSchema(BaseModel):
    DegreeName: Optional[str] = ""
    NormalizeDegree: Optional[str] = ""
    Specialization: Optional[str] = ""
    Date: Optional[str] = ""
    CountryOrInstitute: Optional[str] = ""

# Schema for certification information (used for CV parsing)
class CertificationSchema(BaseModel):
    CertificationName: Optional[str] = ""
    IssuingOrganization: Optional[str] = ""
    IssueDate: Optional[str] = ""

# Schema for professional experience (used for CV parsing)
class ExperienceSchema(BaseModel):
    JobTitle: Optional[str] = ""
    Company: Optional[str] = ""
    Location: Optional[str] = ""
    StartDate: Optional[str] = ""
    EndDate: Optional[str] = ""
    Duration: Optional[str] = ""
    Responsibilities: Optional[List[str]] = Field(default_factory=list)
    Achievements: Optional[List[str]] = Field(default_factory=list)
    ToolsAndTechnologies: Optional[List[str]] = Field(default_factory=list)
    TeamSize: Optional[str] = ""
    RelevanceScore: Optional[str] = ""

# Schema for project information (used for CV parsing)
class ProjectSchema(BaseModel):
    ProjectName: Optional[str] = ""
    Description: Optional[str] = ""
    TechnologiesUsed: Optional[List[str]] = Field(default_factory=list)
    Role: Optional[str] = ""
    Period: Optional[str] = ""
    URL: Optional[str] = ""

# Schema for awards and publications (used for CV parsing)
class AwardPublicationSchema(BaseModel):
    Type: Optional[str] = ""
    Title: Optional[str] = ""
    Description: Optional[str] = ""
    Date: Optional[str] = ""
    PublisherOrIssuer: Optional[str] = ""
    URL: Optional[str] = ""

# Schema for candidate information (used for CV parsing)
class CandidateInfoSchema(BaseModel):
    FullName: Optional[str] = ""
    PhoneNumber: Optional[PhoneNumberSchema] = Field(default_factory=PhoneNumberSchema)
    Email: Optional[str] = ""
    Linkedin: Optional[str] = ""
    Github: Optional[str] = ""
    OtherLinks: Optional[List[str]] = Field(default_factory=list)
    Country: Optional[str] = ""
    Nationalities: Optional[List[str]] = Field(default_factory=list)
    DateOfBirthOrAge: Optional[str] = ""
    Gender: Optional[str] = ""
    MaritalStatus: Optional[str] = ""
    Languages: Optional[List[str]] = Field(default_factory=list)
    CurrentJobTitle: Optional[str] = ""

# Complete parsed resume schema (used for CV parsing)
class ParsedResumeSchema(BaseModel):
    CandidateInfo: CandidateInfoSchema = Field(default_factory=CandidateInfoSchema)
    SuggestedJobs: Optional[List[str]] = Field(default_factory=list)
    Degrees: Optional[List[DegreeSchema]] = Field(default_factory=list)
    Certifications: Optional[List[CertificationSchema]] = Field(default_factory=list)
    HardSkills: Optional[List[str]] = Field(default_factory=list)
    SoftSkills: Optional[List[str]] = Field(default_factory=list)
    ProfessionalExperience: Optional[List[ExperienceSchema]] = Field(default_factory=list)
    Projects: Optional[List[ProjectSchema]] = Field(default_factory=list)
    AwardsAndPublications: Optional[List[AwardPublicationSchema]] = Field(default_factory=list)

# Schema for creating phone numbers
class PhoneNumberCreate(BaseModel):
    number: str
    isd_code: Optional[str] = None
    original_number: Optional[str] = None
    formatted_number: Optional[str] = None
    phone_type: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating languages
class LanguageCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True

# Schema for creating skills
class SkillCreate(BaseModel):
    name: str
    is_hard_skill: Optional[bool] = True

    class Config:
        from_attributes = True

# Schema for creating degrees
class DegreeCreate(BaseModel):
    degree_name: str
    normalize_degree: Optional[str] = None
    specialization: Optional[str] = None
    date: Optional[str] = None
    country_or_institute: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating certifications
class CertificationCreate(BaseModel):
    certification_name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating experiences
class ExperienceCreate(BaseModel):
    job_title: str
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    responsibilities: Optional[List[str]] = Field(default_factory=list)
    achievements: Optional[List[str]] = Field(default_factory=list)
    tools_technologies: Optional[List[str]] = Field(default_factory=list)
    team_size: Optional[str] = None
    relevance_score: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating projects
class ProjectCreate(BaseModel):
    project_name: str
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = Field(default_factory=list)
    role: Optional[str] = None
    period: Optional[str] = None
    url: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating awards and publications
class AwardPublicationCreate(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    publisher_issuer: Optional[str] = None
    url: Optional[str] = None

    class Config:
        from_attributes = True

# Schema for creating suggested jobs
class SuggestedJobCreate(BaseModel):
    job_title: str

    class Config:
        from_attributes = True

# Basic candidate model
class CandidateBase(BaseModel):
    name: str
    email: str
    job_title: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    other_links: Optional[Dict[str, Any]] = None
    country: Optional[str] = None
    nationalities: Optional[List[str]] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    added_by_id: Optional[int] = None

# Schema for creating candidates
class CandidateCreate(CandidateBase):
    phone_numbers: Optional[List[PhoneNumberCreate]] = None
    languages: Optional[List[LanguageCreate]] = None
    hard_skills: Optional[List[SkillCreate]] = None
    soft_skills: Optional[List[SkillCreate]] = None
    degrees: Optional[List[DegreeCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None
    experiences: Optional[List[ExperienceCreate]] = None
    projects: Optional[List[ProjectCreate]] = None
    awards_publications: Optional[List[AwardPublicationCreate]] = None
    suggested_jobs: Optional[List[SuggestedJobCreate]] = None

    class Config:
        from_attributes = True

# Schema for candidate response
class CandidateResponse(CandidateBase):
    id: int
    created_at: Optional[datetime] = None
    phone_numbers: Optional[List[PhoneNumberCreate]] = None
    languages: Optional[List[LanguageCreate]] = None
    hard_skills: Optional[List[SkillCreate]] = None
    soft_skills: Optional[List[SkillCreate]] = None
    degrees: Optional[List[DegreeCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None
    experiences: Optional[List[ExperienceCreate]] = None
    projects: Optional[List[ProjectCreate]] = None
    awards_publications: Optional[List[AwardPublicationCreate]] = None
    suggested_jobs: Optional[List[SuggestedJobCreate]] = None
    added_by: Optional[str] = None  # Username of the uploader

    class Config:
        from_attributes = True

# Schema for CV upload
class CVUpload(BaseModel):
    fileContents: List[str]
    
    class Config:
        from_attributes = True

# Schema for expanded candidate response
class CandidateDetailResponse(BaseModel):
    candidate: CandidateResponse
    resume_data: ParsedResumeSchema
    
    class Config:
        from_attributes = True

# Schema for updating candidates
class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    job_title: Optional[str] = None
    
    class Config:
        from_attributes = True

# For updating specific sections of resume data
class CandidateResumeUpdate(BaseModel):
    section: str  # e.g., "CandidateInfo", "ProfessionalExperience", etc.
    data: Dict[str, Any]  # The updated data for the section
    item_index: Optional[int] = None  # For updating items in lists (experiences, skills, etc.)
    
    class Config:
        arbitrary_types_allowed = True