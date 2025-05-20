from fastapi import APIRouter, Depends, HTTPException, status,Body, Query
from openai import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import traceback
from app.database.postgresql import SessionLocal, get_db
from app.models.user import User
from app.models.job import Job
from app.models.candidate import Candidate, Resume
from app.schemas.job import (
    JobCreate, JobResponse, JobUpdate, 
    CandidateMatchRequest
)
from app.utils.auth import get_current_active_user, get_current_user, get_admin_user
from app.services.job_matching import analyze_candidate_cv_with_job
import logging
import json
from sqlalchemy.orm import Session

from app.services.elasticsearch_service import ElasticsearchService
from app.services.analysis_cache_service import AnalysisCacheService
from app.config.settings import settings
from app.utils.job_utils import extract_comprehensive_job_data, extract_job_fields  # Import the new utility function

router = APIRouter()
logger = logging.getLogger(__name__)

# Create a simplified schema for the new auto-extraction endpoint
class JobCreateAuto(BaseModel):
    description: str
    job_type_etiquette: Optional[str] = "technique"

@router.post("/auto", response_model=Dict[str, Any])
def create_job_auto(
    job_data: JobCreateAuto, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle offre d'emploi avec extraction automatique du titre, des compétences clés et du type de poste"""
    try:
        # Get basic fields (backward compatibility)
        title, competence_phare, job_type_etiquette = extract_job_fields(job_data.description)
        
        # Get comprehensive data with all the skills
        comprehensive_data = extract_comprehensive_job_data(job_data.description)
        
        # Log the extracted information
        logger.info(f"Extracted title: {title}, competence_phare: {competence_phare}, job_type: {job_type_etiquette}")
        
        # Create a new Job object with the extracted fields
        new_job = Job(
            title=title,
            description=job_data.description,
            job_type_etiquette=job_type_etiquette,  # Use the extracted job type
            created_by_id=current_user.id,
            competence_phare=competence_phare
        )
        
        # Add, commit and refresh to get an ID first
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # Now add the additional extracted fields
        # Convert list fields to JSON strings for database storage
        if "technical_skills" in comprehensive_data and comprehensive_data["technical_skills"]:
            new_job.technical_skills = json.dumps(comprehensive_data["technical_skills"])
        
        if "soft_skills" in comprehensive_data and comprehensive_data["soft_skills"]:
            new_job.soft_skills = json.dumps(comprehensive_data["soft_skills"])
        
        if "other_requirements" in comprehensive_data and comprehensive_data["other_requirements"]:
            new_job.other_requirements = json.dumps(comprehensive_data["other_requirements"])
        
        if "benefits" in comprehensive_data and comprehensive_data["benefits"]:
            new_job.benefits = json.dumps(comprehensive_data["benefits"])
            
        if "contract_type" in comprehensive_data and comprehensive_data["contract_type"]:
            new_job.contract_type = comprehensive_data["contract_type"]
            
        if "experience_level" in comprehensive_data and comprehensive_data["experience_level"]:
            new_job.experience_level = comprehensive_data["experience_level"]
            
        if "work_location" in comprehensive_data and comprehensive_data["work_location"]:
            new_job.location = comprehensive_data["work_location"]
            
        # Add additional fields if your Job model supports them
        
        # Commit the updates
        db.commit()
        db.refresh(new_job)
        
        # Build the response with all fields
        response = {
            "id": new_job.id,
            "title": new_job.title,
            "description": new_job.description,
            "job_type_etiquette": new_job.job_type_etiquette,
            "competence_phare": new_job.competence_phare,
            "created_at": new_job.created_at,
            "updated_at": new_job.updated_at,
            "created_by_id": new_job.created_by_id,
            "created_by": current_user.username,
            "extracted_automatically": True  # Flag to indicate automatic extraction
        }
        
        # Add the extracted skills to the response
        if hasattr(new_job, "technical_skills") and new_job.technical_skills:
            try:
                response["technical_skills"] = json.loads(new_job.technical_skills)
            except:
                response["technical_skills"] = []
                
        if hasattr(new_job, "soft_skills") and new_job.soft_skills:
            try:
                response["soft_skills"] = json.loads(new_job.soft_skills)
            except:
                response["soft_skills"] = []
                
        if hasattr(new_job, "other_requirements") and new_job.other_requirements:
            try:
                response["other_requirements"] = json.loads(new_job.other_requirements)
            except:
                response["other_requirements"] = []
                
        if hasattr(new_job, "benefits") and new_job.benefits:
            try:
                response["benefits"] = json.loads(new_job.benefits)
            except:
                response["benefits"] = []
                
        if hasattr(new_job, "contract_type") and new_job.contract_type:
            response["contract_type"] = new_job.contract_type
            
        if hasattr(new_job, "experience_level") and new_job.experience_level:
            response["experience_level"] = new_job.experience_level
            
        if hasattr(new_job, "location") and new_job.location:
            response["location"] = new_job.location
        
        return response
        
    except Exception as e:
        db.rollback()
        # Detailed log
        logger.error(f"ERREUR lors de la création d'emploi auto: {str(e)}")
        logger.error(traceback.format_exc())
        # Return explicit error
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la création de l'offre d'emploi avec extraction automatique: {str(e)}"
        )
# Keep the original create_job endpoint for compatibility
@router.post("/", response_model=Dict[str, Any])
def create_job(
    job_data: JobCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle offre d'emploi"""
    try:
        # If title is not provided, try to extract it using OpenAI
        if not hasattr(job_data, "title") or not job_data.title:
            title, competence_phare, job_type = extract_job_fields(job_data.description)
            job_title = title
            # Use extracted values only if not explicitly provided
            job_competence_phare = job_data.competence_phare if hasattr(job_data, "competence_phare") and job_data.competence_phare else competence_phare
            job_type_etiquette = job_data.job_type_etiquette if hasattr(job_data, "job_type_etiquette") and job_data.job_type_etiquette else job_type
        else:
            job_title = job_data.title
            job_competence_phare = job_data.competence_phare if hasattr(job_data, "competence_phare") else None
            job_type_etiquette = job_data.job_type_etiquette if hasattr(job_data, "job_type_etiquette") else "technique"
        
        new_job = Job(
            title=job_title,
            description=job_data.description,
            job_type_etiquette=job_type_etiquette,
            created_by_id=current_user.id,
            # competence_phare can be NULL, so only define it if present
            competence_phare=job_competence_phare
        )
        
        # Add, commit and refresh the object
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # Build the response manually
        return {
            "id": new_job.id,
            "title": new_job.title,
            "description": new_job.description,
            "job_type_etiquette": new_job.job_type_etiquette,
            "competence_phare": new_job.competence_phare,
            "created_at": new_job.created_at,
            "updated_at": new_job.updated_at,
            "created_by_id": new_job.created_by_id,
            "created_by": current_user.username
        }
    except Exception as e:
        db.rollback()
        # Detailed log
        import traceback
        print(f"ERREUR lors de la création d'emploi: {str(e)}")
        print(traceback.format_exc())
        # Return explicit error
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors de la création de l'offre d'emploi: {str(e)}"
        )
@router.get("/", response_model=List[Dict[str, Any]])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer la liste des offres d'emploi"""
    try:
        # Log pour débogage
        logger.info(f"Tentative de récupération des jobs avec skip={skip}, limit={limit}")
        
        # Version plus robuste de la requête
        jobs = db.query(Job).offset(skip).limit(limit).all()
        logger.info(f"Nombre de jobs trouvés: {len(jobs)}")
        
        # Utiliser une approche plus sécurisée pour créer le résultat
        result = []
        for job in jobs:
            try:
                # Construire manuellement le dictionnaire au lieu d'utiliser from_orm
                job_dict = {
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "competence_phare": job.competence_phare if hasattr(job, "competence_phare") else None,
                    "job_type_etiquette": job.job_type_etiquette if hasattr(job, "job_type_etiquette") else "technique",
                    "created_at": job.created_at,
                    "updated_at": job.updated_at if hasattr(job, "updated_at") else None,
                    "created_by_id": job.created_by_id if hasattr(job, "created_by_id") else None,
                    "created_by": None  # Valeur par défaut
                }
                
                # Essayer de récupérer le créateur avec gestion d'erreur
                if hasattr(job, "created_by_id") and job.created_by_id:
                    try:
                        creator = db.query(User).filter(User.id == job.created_by_id).first()
                        if creator:
                            job_dict["created_by"] = creator.username
                    except Exception as user_error:
                        logger.error(f"Erreur lors de la récupération du créateur du job {job.id}: {str(user_error)}")
                
                result.append(job_dict)
            except Exception as job_error:
                logger.error(f"Erreur lors du traitement du job: {str(job_error)}")
                # Ajouter une version minimale du job en cas d'erreur
                result.append({
                    "id": job.id if hasattr(job, "id") else 0,
                    "title": job.title if hasattr(job, "title") else "Titre inconnu",
                    "description": job.description if hasattr(job, "description") else "Description inconnue",
                    "competence_phare": None,
                    "job_type_etiquette": "technique",
                    "created_at": job.created_at if hasattr(job, "created_at") else datetime.now(),
                    "updated_at": None,
                    "created_by_id": None,
                    "created_by": None
                })
        
        return result
    except Exception as e:
        # Log détaillé de l'erreur pour débogage
        logger.error(f"Erreur lors de la récupération des offres d'emploi: {str(e)}")
        logger.error(traceback.format_exc())  # Log la stack trace
        
        # Retourner une liste vide au lieu de lever une erreur 500
        return []

@router.get("/{job_id}", response_model=Dict[str, Any])
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer une offre d'emploi par son ID"""
    try:
        # Chercher le job dans la base de données
        job = db.query(Job).filter(Job.id == job_id).first()
        
        # Si le job n'existe pas, renvoyer une réponse 404 plus explicite
        if not job:
            # Log l'information
            logger.info(f"Job avec ID {job_id} non trouvé dans la base de données")
            
            # Renvoyer une réponse 404 avec des détails
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Offre d'emploi avec ID {job_id} non trouvée",
                    "error_code": "JOB_NOT_FOUND",
                    "job_id": job_id
                }
            )
        
        # Si le job existe, construire la réponse
        response = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "job_type_etiquette": job.job_type_etiquette if hasattr(job, "job_type_etiquette") else "technique",
            "competence_phare": job.competence_phare if hasattr(job, "competence_phare") else None,
            "created_at": job.created_at,
            "updated_at": job.updated_at if hasattr(job, "updated_at") else None,
            "created_by_id": job.created_by_id if hasattr(job, "created_by_id") else None,
            "created_by": None  # Valeur par défaut
        }
        
        # Add extracted skills to response if they exist
        if hasattr(job, "technical_skills") and job.technical_skills:
            try:
                response["technical_skills"] = json.loads(job.technical_skills)
            except:
                response["technical_skills"] = []
                
        if hasattr(job, "soft_skills") and job.soft_skills:
            try:
                response["soft_skills"] = json.loads(job.soft_skills)
            except:
                response["soft_skills"] = []
                
        if hasattr(job, "other_requirements") and job.other_requirements:
            try:
                response["other_requirements"] = json.loads(job.other_requirements)
            except:
                response["other_requirements"] = []
                
        if hasattr(job, "benefits") and job.benefits:
            try:
                response["benefits"] = json.loads(job.benefits)
            except:
                response["benefits"] = []
                
        if hasattr(job, "contract_type") and job.contract_type:
            response["contract_type"] = job.contract_type
            
        if hasattr(job, "experience_level") and job.experience_level:
            response["experience_level"] = job.experience_level
            
        if hasattr(job, "location") and job.location:
            response["location"] = job.location
        
        # Ajouter le nom du créateur si disponible
        if hasattr(job, "created_by_id") and job.created_by_id:
            creator = db.query(User).filter(User.id == job.created_by_id).first()
            if creator:
                response["created_by"] = creator.username
        
        return response
        
    except HTTPException:
        # Relancer les exceptions HTTP
        raise
    except Exception as e:
        # Log l'erreur
        logger.error(f"Erreur lors de la récupération du job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Renvoyer une erreur 500
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de l'offre d'emploi: {str(e)}"
        )
@router.put("/{job_id}", response_model=Dict[str, Any])
def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mettre à jour une offre d'emploi"""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
            
        # Mettre à jour les champs fournis
        update_data = job_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)
            
        db.commit()
        db.refresh(job)
        
        # Construire manuellement le dictionnaire de réponse
        job_dict = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "competence_phare": job.competence_phare if hasattr(job, "competence_phare") else None,
            "job_type_etiquette": job.job_type_etiquette if hasattr(job, "job_type_etiquette") else "technique",
            "created_at": job.created_at,
            "updated_at": job.updated_at if hasattr(job, "updated_at") else None,
            "created_by_id": job.created_by_id if hasattr(job, "created_by_id") else None,
            "created_by": None  # Valeur par défaut
        }
        
        # Essayer de récupérer le créateur
        if hasattr(job, "created_by_id") and job.created_by_id:
            creator = db.query(User).filter(User.id == job.created_by_id).first()
            if creator:
                job_dict["created_by"] = creator.username
            
        return job_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'offre d'emploi: {str(e)}")
        logger.error(traceback.format_exc())  # Log la stack trace
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour de l'offre d'emploi: {str(e)}")

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Seuls les admins peuvent supprimer
):
    """Supprimer une offre d'emploi"""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
            
        db.delete(job)
        db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'offre d'emploi: {str(e)}")
        logger.error(traceback.format_exc())  # Log la stack trace
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de l'offre d'emploi: {str(e)}")

@router.post("/{job_id}/analyze-candidates", response_model=Dict[str, Any])
def analyze_candidates(
    job_id: int,
    request: CandidateMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyser la correspondance entre des candidats et une offre d'emploi"""
    try:
        # Make sure job_id in URL and body match
        if request.job_id != job_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Le job_id dans le corps de la requête ({request.job_id}) ne correspond pas au job_id dans l'URL ({job_id})"
            )
        
        candidate_ids = request.candidates
        
        if not candidate_ids:
            raise HTTPException(
                status_code=400, 
                detail="Aucun ID de candidat fourni. Veuillez spécifier au moins un ID de candidat."
            )
        
        # Vérifier que l'offre d'emploi existe
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Offre d'emploi non trouvée")
            
        # Call the analyze_candidate_cv_with_job from job_match.py
        from app.services.job_matching import analyze_candidate_cv_with_job as analyze_candidate_cv_with_job_service
        result = analyze_candidate_cv_with_job_service(job_id, candidate_ids, current_user, db)
        
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des candidats: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse des candidats: {str(e)}")
def analyze_candidate_cv_with_job(job_id: int, candidate_ids: List[int], current_user: User, db: Session) -> Dict[str, Any]:
    """
    Analyser les CV des candidats sélectionnés par rapport à une offre d'emploi.
    Si candidate_ids contient "auto", utilise Elasticsearch pour trouver les meilleurs candidats par titre de poste.
    """
    try:
        from app.models.candidate import Candidate, Resume
        from app.models.job import Job
        from app.services.job_matching import JobMatcher
        from app.services.elasticsearch_service import ElasticsearchService
        from app.services.analysis_cache_service import AnalysisCacheService

        logger.info(f"Starting analysis for job_id: {job_id}, candidates: {candidate_ids}")

        # Initialiser le service de cache
        cache_service = AnalysisCacheService(db)

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        job_info = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "competence_phare": job.competence_phare if hasattr(job, "competence_phare") else None,
            "job_type_etiquette": job.job_type_etiquette if hasattr(job, "job_type_etiquette") else "technique"
        }

        # Initialiser le service Elasticsearch
        es_service = ElasticsearchService()
        es_candidates_map = {}  # Pour stocker les scores Elasticsearch

        # Si le mode automatique est demandé ou aucun candidat n'est fourni
        if not candidate_ids or (len(candidate_ids) == 1 and str(candidate_ids[0]).lower() == "auto"):
            logger.info("Auto mode: Using Elasticsearch to find best matching candidates by job title")
            es_result = es_service.filter_candidates_by_job(job_id, min_score=0.5, limit=5, job_info=job_info)
            
            if not es_result or not es_result.get("suggested_candidates"):
                return {
                    "job_info": {
                        "job_id": job.id,
                        "job_title": job.title,
                        "competence_phare": job_info["competence_phare"],
                        "job_type": job_info["job_type_etiquette"]
                    },
                    "total_candidates_analyzed": 0,
                    "analyses": [],
                    "message": "No matching candidates found by Elasticsearch based on job title"
                }
            
            # Extraire les IDs de candidats et leurs scores Elasticsearch
            es_candidates = es_result.get("suggested_candidates", [])
            candidate_ids = []
            
            for c in es_candidates:
                candidate_id = int(c["id"])
                candidate_ids.append(candidate_id)
                # Stocker le score Elasticsearch pour ce candidat
                es_candidates_map[candidate_id] = {
                    "es_score": c.get("es_score", 0.1),  # Valeur par défaut de 0.1
                    "match_reason": c.get("match_reason", "Correspondance par Elasticsearch")
                }
            
            logger.info(f"Elasticsearch found {len(candidate_ids)} potential candidates by job title: {candidate_ids}")

        # Si des candidats spécifiques sont demandés (pas mode auto), obtenir leurs scores Elasticsearch
        elif candidate_ids and candidate_ids[0] != "auto":
            # Pour chaque candidat spécifié, obtenir son score Elasticsearch
            for candidate_id in candidate_ids:
                # Appel individuel pour obtenir le score pour ce candidat spécifique
                es_single_result = es_service.filter_candidates_by_job(
                    job_id, 
                    min_score=0.1, 
                    limit=1, 
                    job_info={"title": job.title, "id": job.id}
                )
                
                if es_single_result and es_single_result.get("suggested_candidates"):
                    for c in es_single_result.get("suggested_candidates", []):
                        if int(c["id"]) == int(candidate_id):
                            es_candidates_map[int(candidate_id)] = {
                                "es_score": c.get("es_score", 0.1),
                                "match_reason": c.get("match_reason", "Correspondance par Elasticsearch")
                            }
                            break
                
                # Si le candidat n'est pas trouvé par Elasticsearch, lui donner un score minimum
                if int(candidate_id) not in es_candidates_map:
                    es_candidates_map[int(candidate_id)] = {
                        "es_score": 0.1,  # Score minimum
                        "match_reason": "Candidat spécifié manuellement"
                    }

        analysis_results = []
        matcher = JobMatcher(openai_api_key=settings.OPENAI_API_KEY)

        for candidate_id in candidate_ids:
            logger.info(f"Processing candidate ID: {candidate_id}")
            try:
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
                if not candidate:
                    logger.warning(f"Candidate {candidate_id} not found")
                    analysis_results.append({
                        "candidate_id": candidate_id,
                        "error": f"Candidate with ID {candidate_id} not found",
                        "status": "failed"
                    })
                    continue

                resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
                if not resume or not resume.resume_json:
                    logger.warning(f"No resume found for candidate {candidate_id}")
                    analysis_results.append({
                        "candidate_id": candidate_id,
                        "error": f"No resume found for candidate ID {candidate_id}",
                        "status": "failed"
                    })
                    continue

                resume_json = resume.resume_json
                if isinstance(resume_json, str):
                    try:
                        resume_json = json.loads(resume_json)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in resume for candidate {candidate_id}: {e}")
                        analysis_results.append({
                            "candidate_id": candidate_id,
                            "error": f"Invalid JSON in resume for candidate ID {candidate_id}",
                            "status": "failed"
                        })
                        continue

                candidate_data = {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "resume_json": resume_json
                }

                # Vérifier si l'analyse est déjà en cache
                cached_analysis = cache_service.get_cached_analysis(job_id, candidate_id)
                
                if cached_analysis:
                    logger.info(f"Using cached analysis for candidate {candidate_id}")
                    gpt_result = cached_analysis
                else:
                    # Si pas en cache, effectuer l'analyse GPT
                    logger.info(f"No cached analysis found for candidate {candidate_id}, performing new analysis")
                    gpt_result = matcher.analyze_candidate(job_info, candidate_data)
                    
                    # Mettre en cache l'analyse
                    cache_success = cache_service.cache_analysis(
                        job_id=job_id,
                        candidate_id=candidate_id,
                        job_title=job.title,
                        candidate_name=candidate.name,
                        analysis=gpt_result
                    )
                    
                    if cache_success:
                        logger.info(f"Analysis for candidate {candidate_id} successfully cached")
                    else:
                        logger.warning(f"Failed to cache analysis for candidate {candidate_id}")

                # Récupérer le score Elasticsearch pour ce candidat
                es_data = es_candidates_map.get(int(candidate_id), {"es_score": 0.1, "match_reason": "Non évalué par Elasticsearch"})
                es_score = es_data["es_score"]
                match_reason = es_data["match_reason"]
                
                # Extraire le score GPT (déjà sous forme de pourcentage)
                gpt_score_str = gpt_result.get("final_score", "0%").replace("%", "")
                gpt_score = float(gpt_score_str) / 100.0  # Convertir en décimal
                
                # Calculer le score combiné (60% GPT + 40% Elasticsearch)
                combined_score = (gpt_score * 0.6) + (es_score * 0.4)
                combined_score_percent = f"{int(combined_score * 100)}%"
                
                # Ajouter les informations Elasticsearch au résultat
                gpt_result["es_score"] = f"{int(es_score * 100)}%"
                gpt_result["es_match_reason"] = match_reason
                gpt_result["combined_score"] = combined_score_percent
                gpt_result["final_score"] = combined_score_percent  # Remplacer le score final par le score combiné
                
                # Ajouter la méthode de combinaison dans les informations
                gpt_result["score_calculation_method"] = "60% GPT + 40% Elasticsearch"
                
                # Mettre à jour l'analyse CV avec le score combiné
                if "cv_analysis" in gpt_result:
                    gpt_result["cv_analysis"]["general_score"] = combined_score_percent
                    gpt_result["cv_analysis"]["es_score"] = f"{int(es_score * 100)}%"
                    gpt_result["cv_analysis"]["gpt_score"] = gpt_result.get("cv_analysis", {}).get("general_score", "0%")
                
                # Ajouter l'information de source si le mode auto était utilisé
                if str(candidate_ids[0]).lower() == "auto":
                    gpt_result["source"] = "elasticsearch_suggestion"
                
                analysis_results.append(gpt_result)
                logger.info(f"Analysis completed for candidate {candidate_id} with combined score {combined_score_percent}")

            except Exception as e:
                logger.error(f"Error processing candidate {candidate_id}: {str(e)}")
                analysis_results.append({
                    "candidate_id": candidate_id,
                    "error": str(e),
                    "status": "failed"
                })

        # Tri des résultats par score combiné (décroissant)
        successful_results = [r for r in analysis_results if r.get("status") == "success"]
        failed_results = [r for r in analysis_results if r.get("status") != "success"]
        
        # Tri des résultats réussis par score combiné
        sorted_successful = sorted(
            successful_results, 
            key=lambda x: int(x.get("combined_score", "0%").replace("%", "")), 
            reverse=True
        )
        
        # Combiner les résultats triés avec les échecs
        sorted_results = sorted_successful + failed_results

        logger.info(f"Completed analysis for {len(analysis_results)} candidates with combined scores")
        return {
            "job_info": {
                "job_id": job.id,
                "job_title": job.title,
                "competence_phare": job.competence_phare if hasattr(job, "competence_phare") else None,
                "job_type": job.job_type_etiquette if hasattr(job, "job_type_etiquette") else "technique"
            },
            "total_candidates_analyzed": len(analysis_results),
            "analyses": sorted_results,  # Résultats triés par score combiné
            "search_method": "auto" if str(candidate_ids[0]).lower() == "auto" else "manual",
            "score_methodology": "Score combiné: 60% analyse GPT + 40% correspondance Elasticsearch"
        }

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Analysis failed: {str(e)}")
@router.delete("/jobs/{job_id}/cache/{candidate_id}")
def invalidate_analysis_cache(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Invalide le cache d'analyse pour un job et un candidat spécifiques.
    Cela forcera une nouvelle analyse lors de la prochaine requête.
    """
    try:
        cache_service = AnalysisCacheService(db)
        success = cache_service.invalidate_cache(job_id=job_id, candidate_id=candidate_id)
        
        if success:
            return {"message": "Cache invalidated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to invalidate cache")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/{job_id}/suggest-candidates")
async def suggest_candidates(
    job_id: int,
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.5, ge=0.1, le=1.0)
):
    """Suggest candidates for a specific job"""
    try:
        # Verify job exists and get job info
        db = SessionLocal()
        job_info = None
        
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise HTTPException(status_code=404, detail=f"Job with id {job_id} not found")
            
            # Create job_info dictionary with necessary information
            job_info = {
                'title': job.title,
                'description': job.description,
                'skills': []
            }
            
            # Extract skills based on your Job model structure
            # This is an example - adjust based on your actual model relationships
            if hasattr(job, 'skills') and job.skills:
                job_info['skills'] = [skill.name for skill in job.skills]
        finally:
            db.close()
        
        # Initialize ElasticsearchService
        es_service = ElasticsearchService()
        
        # Get candidate suggestions with job_info
        result = es_service.filter_candidates_by_job(
            job_id=job_id, 
            limit=limit, 
            min_score=min_score,
            job_info=job_info  # Pass the job_info dictionary
        )
        
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error suggesting candidates for job {job_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/{job_id}/analyze-auto", response_model=Dict[str, Any])
def analyze_candidates_auto(
    job_id: int,
    limit: int = Query(5, description="Maximum number of candidates to analyze"),
    min_score: float = Query(0.6, description="Minimum Elasticsearch score (0-1)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Automatically find and analyze the best candidates by job title using Elasticsearch + OpenAI"""
    # Appeler avec le mode automatique
    return analyze_candidate_cv_with_job(job_id, ["auto"], current_user, db)