import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)

class AnalysisCacheService:
    def __init__(self, db: Session):
        self.db = db
        logger.debug(f"AnalysisCacheService initialized with db: {type(self.db)}")

    def get_cached_analysis(self, job_id: int, candidate_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupérer une analyse mise en cache pour un job et un candidat spécifiques
        """
        try:
            cached = self.db.query(AnalysisCache).filter(
                AnalysisCache.job_id == job_id,
                AnalysisCache.candidate_id == candidate_id
            ).first()
            
            if cached:
                logger.info(f"Cache hit for job_id={job_id}, candidate_id={candidate_id}")
                return json.loads(cached.analysis_json)
            
            logger.info(f"Cache miss for job_id={job_id}, candidate_id={candidate_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached analysis: {str(e)}", exc_info=True)
            return None

    def cache_analysis(self, job_id: int, candidate_id: int, job_title: str, 
                      candidate_name: str, analysis: Dict[str, Any]) -> bool:
        """
        Mettre en cache une analyse
        """
        try:
            logger.debug(f"Attempting to cache analysis for job_id={job_id}, candidate_id={candidate_id}")
            
            # Ensure combined_score is stored as a string with percentage
            if "combined_score" in analysis and not analysis["combined_score"].endswith("%"):
                analysis["combined_score"] = f"{int(float(analysis['combined_score']) * 100)}%"

            # Check for existing entry
            existing = self.db.query(AnalysisCache).filter(
                AnalysisCache.job_id == job_id,
                AnalysisCache.candidate_id == candidate_id
            ).first()

            if existing:
                # Update existing entry
                existing.job_title = job_title
                existing.candidate_name = candidate_name
                existing.analysis_json = json.dumps(analysis)
                logger.info(f"Updated cache for job_id={job_id}, candidate_id={candidate_id}")
            else:
                # Create new entry
                new_cache = AnalysisCache(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    job_title=job_title,
                    candidate_name=candidate_name,
                    analysis_json=json.dumps(analysis)
                )
                self.db.add(new_cache)
                logger.info(f"Created new cache for job_id={job_id}, candidate_id={candidate_id}")

            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to cache analysis for job_id={job_id}, candidate_id={candidate_id}: {str(e)}", exc_info=True)
            self.db.rollback()
            return False

    def invalidate_cache(self, job_id: int = None, candidate_id: int = None) -> bool:
        """
        Invalider le cache pour un job ou un candidat spécifique
        """
        try:
            query = self.db.query(AnalysisCache)
            
            if job_id is not None:
                query = query.filter(AnalysisCache.job_id == job_id)
            
            if candidate_id is not None:
                query = query.filter(AnalysisCache.candidate_id == candidate_id)
            
            if job_id is None and candidate_id is None:
                logger.warning("Attempting to invalidate all cache entries - this is not allowed")
                return False
            
            count = query.delete()
            self.db.commit()
            
            logger.info(f"Invalidated {count} cache entries")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}", exc_info=True)
            self.db.rollback()
            return False