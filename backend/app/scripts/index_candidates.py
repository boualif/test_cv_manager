import logging
import sys
import time
from datetime import datetime
import os
import subprocess

# Importations pour résoudre les relations
from app.models.user import User  # Importez User AVANT Candidate
from app.models.candidate import Candidate
from app.models.job import Job

from app.database.postgresql import SessionLocal
from app.services.elasticsearch_service import ElasticsearchService

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_elasticsearch_cluster():
    """Attempt to fix Elasticsearch cluster issues"""
    logger.info("Attempting to fix Elasticsearch cluster...")
    
    # Try to connect to Elasticsearch and check health
    try:
        es_service = ElasticsearchService()
        health = es_service.es.cluster.health(request_timeout=30)
        
        if health['status'] == 'red':
            logger.warning("Cluster health is RED. Attempting to fix...")
            
            # Try more aggressive recovery methods
            try:
                # Force close all indices
                indices = es_service.es.indices.get(index="*", request_timeout=30)
                for index_name in indices:
                    try:
                        logger.info(f"Forcing close of index {index_name}...")
                        es_service.es.indices.close(index=index_name, request_timeout=60)
                    except Exception as e:
                        logger.error(f"Error closing index {index_name}: {str(e)}")
                
                # Delete the problem index
                try:
                    if es_service.es.indices.exists(index=es_service.index_name):
                        logger.info(f"Deleting problematic index {es_service.index_name}...")
                        es_service.es.indices.delete(index=es_service.index_name, request_timeout=60, ignore_unavailable=True)
                except Exception as e:
                    logger.error(f"Error deleting index: {str(e)}")
                
                # Check health again
                health = es_service.es.cluster.health(request_timeout=30)
                if health['status'] == 'red':
                    logger.error("Cluster is still RED after index operations. A restart might be needed.")
                    
                    # Add code to restart Elasticsearch service (might require admin privileges)
                    if os.name == 'nt':  # Windows
                        logger.info("Attempting to restart Elasticsearch service on Windows...")
                        try:
                            # Try to restart the service
                            subprocess.run(["net", "stop", "elasticsearch-service-x64"], shell=True, check=False)
                            time.sleep(5)
                            subprocess.run(["net", "start", "elasticsearch-service-x64"], shell=True, check=False)
                            logger.info("Elasticsearch service restart attempted")
                            
                            # Wait for service to start
                            time.sleep(20)
                            
                            # Try to connect again
                            es_service = ElasticsearchService()
                            health = es_service.es.cluster.health(request_timeout=30)
                            logger.info(f"Cluster health after restart: {health['status']}")
                        except Exception as e:
                            logger.error(f"Failed to restart Elasticsearch service: {str(e)}")
                    else:  # Linux/Mac
                        logger.info("To restart Elasticsearch on Linux/Mac, run: sudo systemctl restart elasticsearch")
            
            except Exception as e:
                logger.error(f"Error during cluster recovery: {str(e)}")
        
        return es_service, health['status']
    
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        return None, "unknown"

def index_all_candidates():
    """Index all candidates from the database to Elasticsearch"""
    logger.info("Starting indexing of all candidates...")
    
    # First try to fix the cluster
    es_service, health_status = fix_elasticsearch_cluster()
    
    if es_service is None:
        logger.error("Failed to connect to Elasticsearch. Aborting.")
        return False
    
    if health_status == 'red':
        logger.error("Elasticsearch cluster health is still RED. Please restart the Elasticsearch service manually.")
        logger.error("On Windows: restart the 'elasticsearch-service-x64' service")
        logger.error("On Linux: run 'sudo systemctl restart elasticsearch'")
        logger.error("Then try running this script again.")
        return False
    
    # Create or recreate the index
    logger.info("Creating or recreating the index with proper settings...")
    if not es_service.create_index():
        logger.error("Failed to create index. Aborting.")
        return False
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Load all candidates with their relationships
        candidates = db.query(Candidate).all()
        total_candidates = len(candidates)
        logger.info(f"Found {total_candidates} candidates to index")
        
        # Index candidates individually which is more reliable
        success_count = 0
        failed_ids = []
        
        for candidate in candidates:
            try:
                if es_service.index_candidate_from_model(candidate):
                    success_count += 1
                    if success_count % 5 == 0 or success_count == total_candidates:
                        logger.info(f"Progress: {success_count}/{total_candidates} candidates indexed")
                else:
                    failed_ids.append(candidate.id)
                    logger.warning(f"Failed to index candidate ID {candidate.id}")
                
                # Add a small delay between each request
                time.sleep(1)
            
            except Exception as e:
                failed_ids.append(candidate.id)
                logger.error(f"Error indexing candidate ID {candidate.id}: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Indexing completed: {success_count}/{total_candidates} candidates indexed successfully")
        
        if failed_ids:
            logger.warning(f"Failed to index {len(failed_ids)} candidates: {failed_ids}")
    
    except Exception as e:
        logger.error(f"Error during indexing process: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    finally:
        db.close()
        logger.info("Database session closed. Indexing complete")
    
    return True

if __name__ == "__main__":
    try:
        success = index_all_candidates()
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)
