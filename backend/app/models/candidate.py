from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text, Boolean, Table, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.postgresql import Base

# Tables d'association pour les relations many-to-many
candidate_languages = Table(
    'candidate_languages',
    Base.metadata,
    Column('candidate_id', Integer, ForeignKey('candidates.id', ondelete="CASCADE")),
    Column('language_id', Integer, ForeignKey('languages.id', ondelete="CASCADE"))
)

candidate_hard_skills = Table(
    'candidate_hard_skills',
    Base.metadata,
    Column('candidate_id', Integer, ForeignKey('candidates.id', ondelete="CASCADE")),
    Column('skill_id', Integer, ForeignKey('skills.id', ondelete="CASCADE"))
)

candidate_soft_skills = Table(
    'candidate_soft_skills',
    Base.metadata,
    Column('candidate_id', Integer, ForeignKey('candidates.id', ondelete="CASCADE")),
    Column('skill_id', Integer, ForeignKey('skills.id', ondelete="CASCADE"))
)

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    # Added this column to track who added the candidate
    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Informations personnelles
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=True)
    github = Column(String(255), nullable=True)
    linkedin = Column(String(255), nullable=True)
    other_links = Column(JSONB, nullable=True)  # Stocke des liens additionnels
    country = Column(String(100), nullable=True)
    nationalities = Column(JSONB, nullable=True)  # Liste des nationalités
    date_of_birth = Column(String(100), nullable=True)
    gender = Column(String(50), nullable=True)
    marital_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    phone_numbers = relationship("PhoneNumber", back_populates="candidate", cascade="all, delete-orphan")
    degrees = relationship("Degree", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    awards_publications = relationship("AwardPublication", back_populates="candidate", cascade="all, delete-orphan")
    suggested_jobs = relationship("SuggestedJob", back_populates="candidate", cascade="all, delete-orphan")
    
    # Added this relationship to link to the User who added the candidate
    added_by = relationship("User", back_populates="added_candidates")
    
    # Relations many-to-many
    languages = relationship("Language", secondary=candidate_languages, backref="candidates")
    hard_skills = relationship("Skill", secondary=candidate_hard_skills, backref="candidates_hard")
    soft_skills = relationship("Skill", secondary=candidate_soft_skills, backref="candidates_soft")
    
    # Fichier CV original
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    resume_file = Column(LargeBinary, nullable=True)  # Stocke le PDF original
    resume_json = Column(Text, nullable=True)  # Stocke la version JSON complète
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="resumes")


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    number = Column(String(50), nullable=False)
    isd_code = Column(String(10), nullable=True)
    original_number = Column(String(50), nullable=True)
    formatted_number = Column(String(50), nullable=True)
    phone_type = Column(String(20), nullable=True)  # mobile, landline
    location = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="phone_numbers")


class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    is_hard_skill = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Degree(Base):
    __tablename__ = "degrees"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    degree_name = Column(String(255), nullable=False)
    normalize_degree = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    date = Column(String(100), nullable=True)
    country_or_institute = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="degrees")


class Certification(Base):
    __tablename__ = "certifications"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    certification_name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_date = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="certifications")


class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(String(100), nullable=True)
    end_date = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    responsibilities = Column(JSONB, nullable=True)  # Liste des responsabilités
    achievements = Column(JSONB, nullable=True)  # Liste des réalisations
    tools_technologies = Column(JSONB, nullable=True)  # Liste des technologies utilisées
    team_size = Column(String(50), nullable=True)
    relevance_score = Column(String(20), nullable=True)  # High, Medium, Low, Skip
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="experiences")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies_used = Column(JSONB, nullable=True)  # Liste des technologies
    role = Column(String(255), nullable=True)
    period = Column(String(100), nullable=True)
    url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="projects")


class AwardPublication(Base):
    __tablename__ = "awards_publications"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)  # Award ou Publication
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    publisher_issuer = Column(String(255), nullable=True)
    url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="awards_publications")


class SuggestedJob(Base):
    __tablename__ = "suggested_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Candidate", back_populates="suggested_jobs")