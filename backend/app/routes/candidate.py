from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from typing import List
from app.database.postgresql import get_db
from app.schemas.candidate import CVUpload, CandidateCreate, CandidateResponse, CandidateUpdate, CandidateResumeUpdate
from app.models.candidate import Candidate, Resume, Experience
from app.models.user import User, UserActivity
from app.services.cv_parser import parse_cv
from app.services.elasticsearch_service import ElasticsearchService
from app.utils.auth import get_current_user, get_admin_user, get_recruiter_user, get_hr_user, get_cv_upload_user
import base64
import json
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
def index_candidate_background(candidate: Candidate, es_service: ElasticsearchService):
    """Background task to index a candidate in Elasticsearch with comprehensive error handling."""
    candidate_id = candidate.id if candidate else "unknown"
    
    try:
        logger.info(f"Background task started for candidate ID {candidate_id}")
        
        # Ensure the candidate object has all relationships loaded
        from app.database.postgresql import SessionLocal
        from sqlalchemy.orm import joinedload
        
        # Create a new database session for the background task
        db = SessionLocal()
        try:
            # Reload the candidate with all relationships
            candidate_with_relations = db.query(Candidate).options(
                joinedload(Candidate.phone_numbers),
                joinedload(Candidate.languages),
                joinedload(Candidate.hard_skills),
                joinedload(Candidate.soft_skills),
                joinedload(Candidate.degrees),
                joinedload(Candidate.certifications),
                joinedload(Candidate.experiences),
                joinedload(Candidate.projects),
                joinedload(Candidate.awards_publications),
                joinedload(Candidate.suggested_jobs)
            ).filter(Candidate.id == candidate_id).first()
            
            if not candidate_with_relations:
                logger.error(f"Background task: Candidate ID {candidate_id} not found in database")
                return False
                
            logger.info(f"Background task: Loaded candidate {candidate_with_relations.name} with relationships")
            
            # Check Elasticsearch health before indexing
            try:
                health = es_service.es.cluster.health(request_timeout=10)
                logger.info(f"Background task: Elasticsearch health check for candidate {candidate_id}: {health['status']}")
                if health['status'] == 'red':
                    logger.warning(f"Background task: Elasticsearch health is RED for candidate {candidate_id}, attempting to index anyway")
            except Exception as health_error:
                logger.error(f"Background task: Health check failed for candidate {candidate_id}: {str(health_error)}")
                return False
            
            # Attempt to index the candidate with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    success = es_service.index_candidate_from_model(candidate_with_relations)
                    
                    if success:
                        logger.info(f"Background task: Successfully indexed candidate ID {candidate_id} on attempt {attempt + 1}")
                        return True
                    else:
                        logger.warning(f"Background task: Failed to index candidate ID {candidate_id} on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2)  # Wait 2 seconds before retry
                        
                except Exception as index_error:
                    logger.error(f"Background task: Indexing error for candidate ID {candidate_id} on attempt {attempt + 1}: {str(index_error)}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)  # Wait 2 seconds before retry
                    else:
                        import traceback
                        logger.error(traceback.format_exc())
            
            logger.error(f"Background task: Failed to index candidate ID {candidate_id} after {max_retries} attempts")
            return False
                
        finally:
            db.close()
            logger.info(f"Background task: Database session closed for candidate ID {candidate_id}")
            
    except Exception as e:
        logger.error(f"Background task: Unexpected error for candidate ID {candidate_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

@router.post("/elasticsearch/reindex-recent", response_model=dict)
async def reindex_recent_candidates(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reindex the most recently added candidates (last 10)."""
    try:
        # Get the 10 most recent candidates
        recent_candidates = db.query(Candidate).options(
            joinedload(Candidate.phone_numbers),
            joinedload(Candidate.languages),
            joinedload(Candidate.hard_skills),
            joinedload(Candidate.soft_skills),
            joinedload(Candidate.degrees),
            joinedload(Candidate.certifications),
            joinedload(Candidate.experiences),
            joinedload(Candidate.projects),
            joinedload(Candidate.awards_publications),
            joinedload(Candidate.suggested_jobs)
        ).order_by(Candidate.created_at.desc()).limit(10).all()
        
        if not recent_candidates:
            return {"message": "No recent candidates found", "reindexed_count": 0}
        
        # Create ES service
        es_service = ElasticsearchService()
        
        # Schedule background tasks for each candidate
        candidate_ids = []
        for candidate in recent_candidates:
            background_tasks.add_task(index_candidate_background, candidate, es_service)
            candidate_ids.append(candidate.id)
        
        logger.info(f"Scheduled re-indexing for {len(candidate_ids)} recent candidates: {candidate_ids}")
        
        return {
            "message": f"Scheduled re-indexing for {len(candidate_ids)} recent candidates",
            "candidate_ids": candidate_ids,
            "reindexed_count": len(candidate_ids)
        }
        
    except Exception as e:
        logger.error(f"Error scheduling re-indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling re-indexing: {str(e)}")
@router.get("/elasticsearch/status", response_model=dict)
async def get_elasticsearch_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Elasticsearch status and candidate counts."""
    try:
        es_service = ElasticsearchService()
        
        # Get cluster health
        health = es_service.es.cluster.health(request_timeout=10)
        
        # Get index info
        index_exists = es_service.es.indices.exists(index=es_service.index_name)
        
        if index_exists:
            # Get document count from Elasticsearch
            index_stats = es_service.es.indices.stats(index=es_service.index_name, request_timeout=10)
            es_count = index_stats['_all']['primaries']['docs']['count']
        else:
            es_count = 0
        
        # Get database candidate count
        db_count = db.query(Candidate).count()
        
        # Get recent candidates (last 10)
        recent_candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).limit(10).all()
        recent_list = [{"id": c.id, "name": c.name, "created_at": c.created_at.isoformat()} for c in recent_candidates]
        
        return {
            "elasticsearch_available": True,
            "cluster_health": health['status'],
            "index_exists": index_exists,
            "indexed_candidates": es_count,
            "database_candidates": db_count,
            "sync_status": "synced" if es_count == db_count else "out_of_sync",
            "missing_count": max(0, db_count - es_count),
            "recent_candidates": recent_list
        }
        
    except Exception as e:
        logger.error(f"Error checking Elasticsearch status: {str(e)}")
        return {
            "elasticsearch_available": False,
            "error": str(e),
            "indexed_candidates": 0,
            "database_candidates": db.query(Candidate).count() if db else 0,
            "sync_status": "unavailable"
        }
def save_candidate_experiences(db: Session, candidate_id: int, parsed_data: dict) -> None:
    """
    Extracts ProfessionalExperience data from parsed_data and saves it to the experiences table,
    handling various date formats and calculating durations as float (years).
    """
    experiences_data = parsed_data.get("ProfessionalExperience", [])
    
    logger.info(f"Professional Experience count for candidate_id {candidate_id}: {len(experiences_data)}")
    if experiences_data:
        logger.debug(f"First experience: {experiences_data[0]}")
    else:
        logger.debug(f"No ProfessionalExperience data found for candidate_id {candidate_id}")

    # Current date for PRESENT calculations
    current_date = datetime(2025, 5, 16, 14, 6)  # Updated to match current time (02:06 PM CET, May 16, 2025)

    # French month names and abbreviations
    french_months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    for exp_data in experiences_data:
        if not exp_data.get("JobTitle"):
            logger.warning(f"Skipping experience with missing JobTitle for candidate_id {candidate_id}: {exp_data}")
            continue

        # Extract and normalize dates
        start_date = exp_data.get("StartDate", "").strip()
        end_date = exp_data.get("EndDate", "").strip()
        duration = exp_data.get("Duration", "").strip()

        # Normalize end_date to "PRESENT" if it matches common variations
        if end_date.upper() in ["PRESENT", "EN COURS"]:
            end_date = "PRESENT"

        # Calculate duration if not provided or if end_date is PRESENT
        duration_years = 0.0
        if not duration or end_date == "PRESENT":
            try:
                # Try different date formats
                date_formats = [
                    "%B %Y",      # e.g., "March 2024"
                    "%m/%Y",      # e.g., "05/2018"
                    "%Y",         # e.g., "2021"
                    "%B",         # e.g., "Février"
                    "%d/%m/%Y",   # e.g., "07/2022"
                    "%m/%d/%Y"    # Alternative MM/DD/YYYY
                ]
                start = None
                end = None

                # Handle "De mai 2022" format
                start_cleaned = start_date.lower().replace("de ", "").strip()
                end_cleaned = end_date.lower().replace("de ", "").strip() if end_date != "PRESENT" else None

                for fmt in date_formats:
                    try:
                        start = datetime.strptime(start_cleaned, fmt) if start_cleaned else None
                        if end_date != "PRESENT":
                            end = datetime.strptime(end_cleaned, fmt) if end_cleaned else None
                        break
                    except ValueError:
                        continue

                # Try French month names
                if not start:
                    start_parts = start_cleaned.split()
                    if len(start_parts) >= 2:  # e.g., "mai 2022"
                        start_month = french_months.get(start_parts[0], 1)
                        start_year = int(start_parts[1])
                        start = datetime(start_year, start_month, 1)
                    elif len(start_parts) == 1 and start_parts[0].isdigit():  # e.g., "2021"
                        start = datetime(int(start_parts[0]), 1, 1)

                if end_date != "PRESENT" and not end:
                    end_parts = end_cleaned.split()
                    if len(end_parts) >= 2:  # e.g., "août 2023"
                        end_month = french_months.get(end_parts[0], 1)
                        end_year = int(end_parts[1])
                        end = datetime(end_year, end_month, 1)
                    elif len(end_parts) == 1 and end_parts[0].isdigit():  # e.g., "2023"
                        end = datetime(int(end_parts[0]), 12, 31)

                # Calculate duration in years
                if start and end_date == "PRESENT":
                    months = (current_date.year - start.year) * 12 + current_date.month - start.month
                    if current_date.day < start.day:
                        months -= 1
                    duration_years = round(months / 12.0, 2)
                elif start and end:
                    months = (end.year - start.year) * 12 + end.month - start.month
                    if end.day < start.day:
                        months -= 1
                    duration_years = round(months / 12.0, 2)
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing dates for {start_date} to {end_date}: {str(e)}")
                duration_years = 0.0

        # Parse duration if provided (e.g., "4 ans", "6 mois")
        if duration and duration_years == 0.0:
            duration_match = re.search(r'(\d+)\s*(years|ans|months|mois)', duration.lower())
            if duration_match:
                num = int(duration_match.group(1))
                unit = duration_match.group(2)
                if unit in ["years", "ans"]:
                    duration_years = float(num)
                elif unit in ["months", "mois"]:
                    duration_years = round(num / 12.0, 2)

        experience = Experience(
            candidate_id=candidate_id,
            job_title=exp_data.get("JobTitle", ""),
            company=exp_data.get("Company", ""),
            location=exp_data.get("Location", ""),
            start_date=start_date,
            end_date=end_date,
            duration=duration_years,  # Store as float (years)
            responsibilities=exp_data.get("Responsibilities", []),
            achievements=exp_data.get("Achievements", []),
            tools_technologies=exp_data.get("ToolsAndTechnologies", []),
            team_size=exp_data.get("TeamSize", ""),
            relevance_score=exp_data.get("RelevanceScore", "")
        )
        db.add(experience)
        logger.info(f"Saved experience: {exp_data.get('JobTitle')} with duration {duration_years} years for candidate_id {candidate_id}")
    
    db.commit()

@router.post("/cv/add", response_model=dict)
async def post_cv(
    upload: CVUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_cv_upload_user)
):
    logger.info(f"Received upload request with {len(upload.fileContents)} files")
    results = []
    duplicates = []
    error_count = 0

    # Create Elasticsearch service instance once
    try:
        es_service = ElasticsearchService()
        health = es_service.es.cluster.health(request_timeout=5)
        es_available = health['status'] != 'red'
        if not es_available:
            logger.warning("Elasticsearch health is RED, automatic indexing may fail")
        else:
            logger.info(f"Elasticsearch is available, health: {health['status']}")
    except Exception as e:
        logger.error(f"Elasticsearch not available: {str(e)}")
        es_available = False

    # Strategy: For multiple uploads, use immediate indexing to avoid background task issues
    use_immediate_indexing = len(upload.fileContents) > 1
    if use_immediate_indexing:
        logger.info(f"Multiple files detected ({len(upload.fileContents)}), using immediate indexing")
    
    candidates_to_index = []  # Store candidates for batch background indexing

    for idx, base64_data in enumerate(upload.fileContents):
        try:
            if not base64_data:
                error_count += 1
                logger.warning(f"Empty data for file {idx}")
                continue

            logger.info(f"Processing file {idx}, data length: {len(base64_data)}")
            binary_data = base64.b64decode(base64_data)
            
            parsed_data = parse_cv(binary_data)
            candidate_info = parsed_data.get("CandidateInfo", {})

            candidate_email = candidate_info.get("Email", "").lower()
            candidate_name = candidate_info.get("FullName", "").lower()

            existing_candidate = db.query(Candidate).filter(
                (func.lower(Candidate.email) == candidate_email) |
                (func.lower(Candidate.name) == candidate_name)
            ).first()

            if existing_candidate:
                logger.info(f"Duplicate candidate found: {candidate_name}")
                duplicates.append({
                    "file_index": idx,
                    "name": candidate_name,
                    "email": candidate_email
                })
                continue

            candidate = Candidate(
                name=candidate_info.get("FullName", "Not Provided"),
                email=candidate_info.get("Email", "Not Provided"),
                job_title=candidate_info.get("CurrentJobTitle", "Not Provided"),
                added_by_id=current_user.id
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            logger.info(f"Created candidate ID {candidate.id}: {candidate.name}")

            try:
                resume_json_str = json.dumps(parsed_data, ensure_ascii=False)
                
                resume = Resume(
                    candidate_id=candidate.id,
                    resume_file=binary_data,
                    resume_json=resume_json_str
                )
                db.add(resume)
                db.commit()
                logger.info(f"Saved resume for candidate ID {candidate.id}")

                save_candidate_experiences(db, candidate.id, parsed_data)
                logger.info(f"Saved experiences for candidate ID {candidate.id}")

                # Load candidate with all relationships for indexing
                candidate_with_relations = db.query(Candidate).options(
                    joinedload(Candidate.phone_numbers),
                    joinedload(Candidate.languages),
                    joinedload(Candidate.hard_skills),
                    joinedload(Candidate.soft_skills),
                    joinedload(Candidate.degrees),
                    joinedload(Candidate.certifications),
                    joinedload(Candidate.experiences),
                    joinedload(Candidate.projects),
                    joinedload(Candidate.awards_publications),
                    joinedload(Candidate.suggested_jobs)
                ).filter(Candidate.id == candidate.id).first()

                # Choose indexing strategy
                indexed = False
                if es_available and candidate_with_relations:
                    if use_immediate_indexing:
                        # Immediate indexing for multiple uploads
                        try:
                            indexed = es_service.index_candidate_from_model(candidate_with_relations)
                            if indexed:
                                logger.info(f"Successfully indexed candidate ID {candidate.id} immediately")
                            else:
                                logger.warning(f"Failed to index candidate ID {candidate.id} immediately")
                        except Exception as index_error:
                            logger.error(f"Error indexing candidate ID {candidate.id} immediately: {str(index_error)}")
                    else:
                        # Background indexing for single uploads
                        background_tasks.add_task(index_candidate_background, candidate_with_relations, es_service)
                        logger.info(f"Scheduled background indexing for candidate ID {candidate.id}")
                        indexed = True  # Assume it will succeed
                else:
                    logger.warning(f"Skipping indexing for candidate ID {candidate.id} - ES available: {es_available}")

                activity = UserActivity(
                    user_id=current_user.id,
                    activity_type="UPLOAD_CV",
                    description=f"User uploaded CV for candidate: {candidate.name}"
                )
                db.add(activity)
                db.commit()

                results.append({
                    "file_name": idx,
                    "candidate_id": candidate.id,
                    "indexed": indexed,
                    "indexing_method": "immediate" if use_immediate_indexing else "background"
                })
                
            except Exception as db_error:
                logger.error(f"Database error for file {idx}: {str(db_error)}")
                import traceback
                logger.error(traceback.format_exc())
                db.rollback()
                db.delete(candidate)
                db.commit()
                error_count += 1
                continue

        except Exception as e:
            logger.error(f"Error processing file {idx}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            error_count += 1
            continue

    logger.info(f"CV upload completed: {len(results)} successful, {len(duplicates)} duplicates, {error_count} errors")
    return {
        "success": results,
        "duplicates": duplicates,
        "error_count": error_count,
        "elasticsearch_available": es_available,
        "indexing_method": "immediate" if use_immediate_indexing else "background"
    }
# [Rest of the routes unchanged]
@router.get("/", response_model=List[CandidateResponse])
async def get_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="VIEW_CANDIDATES",
        description="User viewed candidates list"
    )
    db.add(activity)
    db.commit()
    
    candidates = db.query(Candidate).all()
    
    candidates_with_users = []
    for candidate in candidates:
        user_name = "Non spécifié"
        if candidate.added_by:
            user_name = candidate.added_by.username
                
        candidate_dict = {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "job_title": candidate.job_title,
            "created_at": candidate.created_at,
            "added_by": user_name
        }
        candidates_with_users.append(candidate_dict)
    
    return candidates_with_users

@router.get("/candidates/with-uploader/{candidate_id}", response_model=dict)
async def get_candidates_with_uploader(
    candidate_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="VIEW_CANDIDATE",
        description=f"User viewed candidate profile: {candidate.name}"
    )
    db.add(activity)
    db.commit()
    
    resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
    resume_data = {}
    if resume and resume.resume_json:
        if isinstance(resume.resume_json, str):
            try:
                resume_data = json.loads(resume.resume_json)
            except:
                resume_data = {"CandidateInfo": {}}
        else:
            resume_data = resume.resume_json
    
    return {
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "job_title": candidate.job_title,
            "created_at": candidate.created_at
        },
        "resume_data": resume_data
    }

@router.get("/{candidate_id}/resume", response_class=StreamingResponse)
async def get_candidate_resume(
    candidate_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
    if not resume or not resume.resume_file:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="VIEW_RESUME",
        description=f"User viewed resume for candidate ID: {candidate_id}"
    )
    db.add(activity)
    db.commit()
    
    pdf_file = BytesIO(resume.resume_file)
    pdf_file.seek(0)
    
    return StreamingResponse(
        pdf_file, 
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=candidate_{candidate_id}_resume.pdf"
        }
    )

@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    candidate_data: CandidateUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Update candidate data
    update_data = candidate_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(candidate, key, value)
    
    db.commit()
    
    # Load candidate with all relationships for re-indexing
    candidate_with_relations = db.query(Candidate).options(
        joinedload(Candidate.phone_numbers),
        joinedload(Candidate.languages),
        joinedload(Candidate.hard_skills),
        joinedload(Candidate.soft_skills),
        joinedload(Candidate.degrees),
        joinedload(Candidate.certifications),
        joinedload(Candidate.experiences),
        joinedload(Candidate.projects),
        joinedload(Candidate.awards_publications),
        joinedload(Candidate.suggested_jobs)
    ).filter(Candidate.id == candidate_id).first()
    
    # Schedule automatic re-indexing
    es_service = ElasticsearchService()
    background_tasks.add_task(index_candidate_background, candidate_with_relations, es_service)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="UPDATE_CANDIDATE",
        description=f"User updated candidate: {candidate.name}"
    )
    db.add(activity)
    db.commit()
    
    db.refresh(candidate)
    return candidate
@router.put("/{candidate_id}/resume", response_model=dict)
async def update_candidate_resume(
    candidate_id: int,
    update_data: CandidateResumeUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Update resume data (existing code)
    current_data = {}
    if resume.resume_json:
        try:
            if isinstance(resume.resume_json, str):
                current_data = json.loads(resume.resume_json)
            else:
                current_data = resume.resume_json
        except:
            current_data = {}
    
    section = update_data.section
    new_data = update_data.data
    item_index = update_data.item_index
    
    if item_index is not None and section in current_data and isinstance(current_data[section], list):
        while len(current_data[section]) <= item_index:
            current_data[section].append({})
        current_data[section][item_index] = new_data
    elif section in current_data and isinstance(current_data[section], list) and isinstance(new_data, list):
        current_data[section] = new_data
    elif section in current_data and isinstance(current_data[section], dict) and isinstance(new_data, dict):
        for key, value in new_data.items():
            current_data[section][key] = value
    else:
        current_data[section] = new_data
    
    resume.resume_json = json.dumps(current_data, ensure_ascii=False)
    db.commit()
    
    # If the update affects experience data, update the experiences table and re-index
    if section == "ProfessionalExperience":
        # Delete existing experiences
        db.query(Experience).filter(Experience.candidate_id == candidate_id).delete()
        db.commit()
        
        # Save updated experiences
        save_candidate_experiences(db, candidate_id, current_data)
    
    # Load candidate with all relationships for re-indexing
    candidate_with_relations = db.query(Candidate).options(
        joinedload(Candidate.phone_numbers),
        joinedload(Candidate.languages),
        joinedload(Candidate.hard_skills),
        joinedload(Candidate.soft_skills),
        joinedload(Candidate.degrees),
        joinedload(Candidate.certifications),
        joinedload(Candidate.experiences),
        joinedload(Candidate.projects),
        joinedload(Candidate.awards_publications),
        joinedload(Candidate.suggested_jobs)
    ).filter(Candidate.id == candidate_id).first()
    
    # Schedule automatic re-indexing
    es_service = ElasticsearchService()
    background_tasks.add_task(index_candidate_background, candidate_with_relations, es_service)
    
    # Log activity
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="UPDATE_RESUME",
        description=f"User updated resume section {section} for candidate: {candidate.name if candidate else candidate_id}"
    )
    db.add(activity)
    db.commit()
    
    return {"message": f"Resume section {section} updated successfully", "updated_section": section}
@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    candidate_name = candidate.name
    
    db.query(Resume).filter(Resume.candidate_id == candidate_id).delete()
    db.delete(candidate)
    
    activity = UserActivity(
        user_id=current_user.id,
        activity_type="DELETE_CANDIDATE",
        description=f"User deleted candidate: {candidate_name}"
    )
    db.add(activity)
    
    db.commit()
    
    return None
