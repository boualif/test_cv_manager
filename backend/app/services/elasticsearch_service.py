import logging
from elasticsearch import Elasticsearch, RequestError, TransportError, ConnectionError as ESConnectionError
from elasticsearch.helpers import bulk
from elasticsearch import ConnectionTimeout
import time
from datetime import datetime
from app.models.candidate import Candidate
from app.models.job import Job
from app.database.postgresql import SessionLocal
import os

# Configuration du logger
logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self, host=None):
        self.index_name = "candidates"
        self.es_available = True
        
        # CORRECTION : Utiliser l'URL complète avec le protocole
        elasticsearch_url = host or os.getenv("ELASTICSEARCH_URL", "https://orelservices-search-7419791421.us-east-1.bonsaisearch.net:443")
        username = os.getenv("ELASTICSEARCH_USERNAME", "tgs5qdc5ph")
        password = os.getenv("ELASTICSEARCH_PASSWORD", "j5qcp06xrl")
        
        try:
            # CORRECTION : Configuration améliorée pour Bonsai
            self.es = Elasticsearch(
                hosts=[elasticsearch_url],
                basic_auth=(username, password),
                request_timeout=30,
                retry_on_timeout=True,
                max_retries=3,
                verify_certs=True,  # CHANGÉ : Active la vérification SSL pour Bonsai
                ssl_show_warn=False,
                # CORRECTION : Headers pour compatibilité
                headers={'Content-Type': 'application/json'},
                # SUPPRIMÉ : ca_certs=False (pas recommandé pour production)
            )
            
            # Test de connexion
            info = self.es.info()
            logger.info(f"Connected to Elasticsearch: {info.get('version', {}).get('number', 'Unknown')} at {elasticsearch_url}")
            
            # Vérification de la santé du cluster
            health = self.es.cluster.health()
            logger.info(f"Cluster health: {health['status']}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            self.es_available = False
            logger.warning("Elasticsearch will be disabled due to connection issues.")
            
            # Classe dummy pour éviter les erreurs
            self.es = self._create_dummy_es()
    
    def _create_dummy_es(self):
        """Crée un objet ES factice pour éviter les erreurs quand ES n'est pas disponible"""
        class DummyES:
            def __init__(self):
                self.indices = DummyIndices()
                self.cluster = DummyCluster()
                
            def index(self, *args, **kwargs):
                return {"result": "created", "_id": "dummy-id"}
                
            def search(self, *args, **kwargs):
                return {"hits": {"total": {"value": 0}, "hits": []}}
                
            def get(self, *args, **kwargs):
                return {"_id": "dummy-id", "_source": {}}
            
            def info(self):
                return {"version": {"number": "dummy"}}
        
        class DummyIndices:
            def exists(self, *args, **kwargs):
                return False
                
            def create(self, *args, **kwargs):
                return {"acknowledged": True}
                
            def delete(self, *args, **kwargs):
                return {"acknowledged": True}
        
        class DummyCluster:
            def health(self, *args, **kwargs):
                return {"status": "yellow", "number_of_nodes": 1}
        
        return DummyES()

    # Rest of the class remains unchanged
    def _attempt_cluster_recovery(self):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping cluster recovery")
            return
        
        logger.info("Attempting to recover cluster health...")
        try:
            indices = self.es.indices.get(index="*", request_timeout=30)
            for index_name in indices:
                try:
                    logger.info(f"Closing index {index_name}...")
                    self.es.indices.close(index=index_name, request_timeout=60)
                    logger.info(f"Opening index {index_name}...")
                    self.es.indices.open(index=index_name, request_timeout=60)
                    logger.info(f"Successfully reopened index {index_name}")
                except Exception as e:
                    logger.error(f"Error recovering index {index_name}: {str(e)}")
            health = self.es.cluster.health(request_timeout=30)
            logger.info(f"Cluster health after recovery: {health['status']}")
        except Exception as e:
            logger.error(f"Error during cluster recovery attempt: {str(e)}")

    def create_index(self):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping index creation")
            return False
            
        try:
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,  # Bonsai OSS single-node setup
                    "analysis": {
                        "analyzer": {
                            "custom_analyzer": {
                                "type": "standard",
                                "stopwords": "_english_"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "text", "analyzer": "custom_analyzer"},
                        "email": {"type": "keyword"},
                        "job_title": {"type": "text"},
                        "github": {"type": "keyword"},
                        "linkedin": {"type": "keyword"},
                        "other_links": {"type": "object"},
                        "country": {"type": "keyword"},
                        "nationalities": {"type": "keyword"},
                        "date_of_birth": {"type": "keyword"},
                        "gender": {"type": "keyword"},
                        "marital_status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "phone_numbers": {
                            "type": "nested",
                            "properties": {
                                "number": {"type": "keyword"},
                                "isd_code": {"type": "keyword"},
                                "original_number": {"type": "keyword"},
                                "formatted_number": {"type": "keyword"},
                                "phone_type": {"type": "keyword"},
                                "location": {"type": "keyword"}
                            }
                        },
                        "languages": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"}
                            }
                        },
                        "hard_skills": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"}
                            }
                        },
                        "soft_skills": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"}
                            }
                        },
                        "degrees": {
                            "type": "nested",
                            "properties": {
                                "degree_name": {"type": "text"},
                                "normalize_degree": {"type": "text"},
                                "specialization": {"type": "text"},
                                "date": {"type": "keyword"},
                                "country_or_institute": {"type": "keyword"}
                            }
                        },
                        "certifications": {
                            "type": "nested",
                            "properties": {
                                "certification_name": {"type": "text"},
                                "issuing_organization": {"type": "text"},
                                "issue_date": {"type": "keyword"}
                            }
                        },
                        "experiences": {
                            "type": "nested",
                            "properties": {
                                "job_title": {"type": "text"},
                                "company": {"type": "text"},
                                "location": {"type": "keyword"},
                                "start_date": {"type": "keyword"},
                                "end_date": {"type": "keyword"},
                                "duration": {"type": "keyword"},
                                "responsibilities": {"type": "text"},
                                "achievements": {"type": "text"},
                                "tools_technologies": {"type": "keyword"},
                                "team_size": {"type": "keyword"},
                                "relevance_score": {"type": "keyword"}
                            }
                        },
                        "projects": {
                            "type": "nested",
                            "properties": {
                                "project_name": {"type": "text"},
                                "description": {"type": "text"},
                                "technologies_used": {"type": "keyword"},
                                "role": {"type": "text"},
                                "period": {"type": "keyword"},
                                "url": {"type": "keyword"}
                            }
                        },
                        "awards_publications": {
                            "type": "nested",
                            "properties": {
                                "type": {"type": "keyword"},
                                "title": {"type": "text"},
                                "description": {"type": "text"},
                                "date": {"type": "keyword"},
                                "publisher_issuer": {"type": "text"},
                                "url": {"type": "keyword"}
                            }
                        },
                        "suggested_jobs": {
                            "type": "nested",
                            "properties": {
                                "job_title": {"type": "text"}
                            }
                        }
                    }
                }
            }

            if self.es.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} exists, deleting to ensure proper settings.")
                self.es.indices.delete(index=self.index_name)
                logger.info(f"Index {self.index_name} deleted successfully.")
            
            self.es.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Index {self.index_name} created successfully with 0 replicas")
            self.es.cluster.health(index=self.index_name, wait_for_status="yellow", timeout="60s")
            logger.info(f"Index {self.index_name} is ready for operations")
            return True
        except RequestError as e:
            logger.error(f"Error creating index: {e.info}")
            return False
        except TimeoutError as te:
            logger.error(f"Timeout error creating index: {str(te)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating index: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def diagnose_elasticsearch(self):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping diagnosis")
            return False
            
        try:
            health = self.es.cluster.health()
            logger.info(f"Cluster health: {health['status']}")
            logger.info(f"Number of nodes: {health['number_of_nodes']}")
            logger.info(f"Unassigned shards: {health['unassigned_shards']}")
            node_stats = self.es.nodes.stats()
            for node_id, stats in node_stats['nodes'].items():
                logger.info(f"Node {node_id} JVM heap: {stats['jvm']['mem']['heap_used_percent']}% used")
                logger.info(f"Node {node_id} CPU: {stats.get('os', {}).get('cpu', {}).get('percent', 'N/A')}%")
                logger.info(f"Node {node_id} disk: {stats.get('fs', {}).get('total', {}).get('available_in_bytes', 0) / (1024**3):.2f} GB free")
            if self.es.indices.exists(index=self.index_name):
                index_stats = self.es.indices.stats(index=self.index_name)
                logger.info(f"Index {self.index_name} docs: {index_stats['_all']['primaries']['docs']['count']}")
                logger.info(f"Index {self.index_name} size: {index_stats['_all']['primaries']['store']['size_in_bytes'] / (1024**2):.2f} MB")
            return True
        except Exception as e:
            logger.error(f"Elasticsearch diagnosis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def index_minimal_test_document(self):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping test document indexing")
            return False
            
        try:
            test_doc = {
                "test_field": "This is a test document",
                "timestamp": datetime.now().isoformat()
            }
            result = self.es.index(
                index=self.index_name,
                body=test_doc,
                refresh=True
            )
            logger.info(f"Test document indexed successfully: {result}")
            get_result = self.es.get(
                index=self.index_name,
                id=result['_id']
            )
            logger.info(f"Test document retrieved successfully")
            return True
        except Exception as e:
            logger.error(f"Test document indexing failed: {str(e)}")
            return False

    def index_candidate_from_model(self, candidate: Candidate):
        if not self.es_available:
            logger.info(f"Elasticsearch is not available, skipping indexing for candidate {candidate.id}")
            return False
            
        try:
            doc = {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "job_title": candidate.job_title,
                "github": candidate.github,
                "linkedin": candidate.linkedin,
                "other_links": candidate.other_links,
                "country": candidate.country,
                "nationalities": candidate.nationalities,
                "date_of_birth": candidate.date_of_birth,
                "gender": candidate.gender,
                "marital_status": candidate.marital_status,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "phone_numbers": [
                    {
                        "number": pn.number,
                        "isd_code": pn.isd_code,
                        "original_number": pn.original_number,
                        "formatted_number": pn.formatted_number,
                        "phone_type": pn.phone_type,
                        "location": pn.location
                    } for pn in candidate.phone_numbers
                ],
                "languages": [{"name": lang.name} for lang in candidate.languages],
                "hard_skills": [{"name": skill.name} for skill in candidate.hard_skills],
                "soft_skills": [{"name": skill.name} for skill in candidate.soft_skills],
                "degrees": [
                    {
                        "degree_name": deg.degree_name,
                        "normalize_degree": deg.normalize_degree,
                        "specialization": deg.specialization,
                        "date": deg.date,
                        "country_or_institute": deg.country_or_institute
                    } for deg in candidate.degrees
                ],
                "certifications": [
                    {
                        "certification_name": cert.certification_name,
                        "issuing_organization": cert.issuing_organization,
                        "issue_date": cert.issue_date
                    } for cert in candidate.certifications
                ],
                "experiences": [
                    {
                        "job_title": exp.job_title,
                        "company": exp.company,
                        "location": exp.location,
                        "start_date": exp.start_date,
                        "end_date": exp.end_date,
                        "duration": exp.duration,
                        "responsibilities": exp.responsibilities,
                        "achievements": exp.achievements,
                        "tools_technologies": exp.tools_technologies,
                        "team_size": exp.team_size,
                        "relevance_score": exp.relevance_score
                    } for exp in candidate.experiences
                ],
                "projects": [
                    {
                        "project_name": proj.project_name,
                        "description": proj.description,
                        "technologies_used": proj.technologies_used,
                        "role": proj.role,
                        "period": proj.period,
                        "url": proj.url
                    } for proj in candidate.projects
                ],
                "awards_publications": [
                    {
                        "type": ap.type,
                        "title": ap.title,
                        "description": ap.description,
                        "date": ap.date,
                        "publisher_issuer": ap.publisher_issuer,
                        "url": ap.url
                    } for ap in candidate.awards_publications
                ],
                "suggested_jobs": [
                    {"job_title": job.job_title} for job in candidate.suggested_jobs
                ]
            }
            for attempt in range(3):
                try:
                    result = self.es.index(
                        index=self.index_name,
                        id=candidate.id,
                        body=doc,
                        refresh=True
                    )
                    logger.info(f"Indexed candidate ID {candidate.id}")
                    return True
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"Attempt {attempt+1} failed for candidate ID {candidate.id}: {str(e)}")
                        time.sleep(2)
                    else:
                        logger.error(f"Failed to index candidate ID {candidate.id} after 3 attempts: {str(e)}")
                        return False
        except Exception as e:
            logger.error(f"Failed to index candidate ID {candidate.id}: {str(e)}")
            return False

    def bulk_index_candidates(self, candidates, batch_size=3):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping bulk indexing")
            return 0, candidates
            
        success_count = 0
        failed_candidates = []
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i+batch_size]
            actions = []
            candidate_map = {}
            for candidate in batch:
                doc = {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "job_title": candidate.job_title,
                    "github": candidate.github,
                    "linkedin": candidate.linkedin,
                    "other_links": candidate.other_links,
                    "country": candidate.country,
                    "nationalities": candidate.nationalities,
                    "date_of_birth": candidate.date_of_birth,
                    "gender": candidate.gender,
                    "marital_status": candidate.marital_status,
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                    "phone_numbers": [
                        {
                            "number": pn.number,
                            "isd_code": pn.isd_code,
                            "original_number": pn.original_number,
                            "formatted_number": pn.formatted_number,
                            "phone_type": pn.phone_type,
                            "location": pn.location
                        } for pn in candidate.phone_numbers
                    ],
                    "languages": [{"name": lang.name} for lang in candidate.languages],
                    "hard_skills": [{"name": skill.name} for skill in candidate.hard_skills],
                    "soft_skills": [{"name": skill.name} for skill in candidate.soft_skills],
                    "degrees": [
                        {
                            "degree_name": deg.degree_name,
                            "normalize_degree": deg.normalize_degree,
                            "specialization": deg.specialization,
                            "date": deg.date,
                            "country_or_institute": deg.country_or_institute
                        } for deg in candidate.degrees
                    ],
                    "certifications": [
                        {
                            "certification_name": cert.certification_name,
                            "issuing_organization": cert.issuing_organization,
                            "issue_date": cert.issue_date
                        } for cert in candidate.certifications
                    ],
                    "experiences": [
                        {
                            "job_title": exp.job_title,
                            "company": exp.company,
                            "location": exp.location,
                            "start_date": exp.start_date,
                            "end_date": exp.end_date,
                            "duration": exp.duration,
                            "responsibilities": exp.responsibilities,
                            "achievements": exp.achievements,
                            "tools_technologies": exp.tools_technologies,
                            "team_size": exp.team_size,
                            "relevance_score": exp.relevance_score
                        } for exp in candidate.experiences
                    ],
                    "projects": [
                        {
                            "project_name": proj.project_name,
                            "description": proj.description,
                            "technologies_used": proj.technologies_used,
                            "role": proj.role,
                            "period": proj.period,
                            "url": proj.url
                        } for proj in candidate.projects
                    ],
                    "awards_publications": [
                        {
                            "type": ap.type,
                            "title": ap.title,
                            "description": ap.description,
                            "date": ap.date,
                            "publisher_issuer": ap.publisher_issuer,
                            "url": ap.url
                        } for ap in candidate.awards_publications
                    ],
                    "suggested_jobs": [
                        {"job_title": job.job_title} for job in candidate.suggested_jobs
                    ]
                }
                action = {
                    "_index": self.index_name,
                    "_id": candidate.id,
                    "_source": doc
                }
                actions.append(action)
                candidate_map[str(candidate.id)] = candidate
            
            if not actions:
                continue
                
            for attempt in range(3):
                try:
                    health = self.es.cluster.health()
                    if health['status'] == 'red':
                        logger.warning(f"Cluster health is RED before batch {i//batch_size + 1}. Attempting recovery...")
                        self._attempt_cluster_recovery()
                        health = self.es.cluster.health()
                        if health['status'] == 'red':
                            logger.error("Cluster still unhealthy. Trying individual indexing instead.")
                            for candidate in batch:
                                if self.index_candidate_from_model(candidate):
                                    success_count += 1
                                else:
                                    failed_candidates.append(candidate)
                            break
                    
                    success, failed = bulk(
                        self.es,
                        actions,
                        refresh=True,
                        raise_on_error=False,
                        stats_only=False
                    )
                    successful_docs = sum(1 for item in success if 'index' in item and item['index'].get('status') in [200, 201])
                    failed_ids = [item['index']['_id'] for item in failed if 'index' in item]
                    for item in failed:
                        if 'index' in item:
                            failed_id = item['index'].get('_id')
                            error = item['index'].get('error', {})
                            logger.error(f"Document ID {failed_id} failed: {error.get('type')} - {error.get('reason')}")
                    success_count += successful_docs
                    logger.info(f"Batch {i//batch_size + 1}: Indexed {successful_docs}/{len(batch)} candidates")
                    for candidate in batch:
                        if str(candidate.id) in failed_ids:
                            failed_candidates.append(candidate)
                    break
                except ConnectionTimeout as ct:
                    logger.warning(f"Timeout on batch {i//batch_size + 1}, attempt {attempt+1}/3: {str(ct)}")
                    if attempt < 2:
                        time.sleep(5)
                    else:
                        logger.error(f"Failed to index batch after 3 attempts")
                        failed_candidates.extend(batch)
                except Exception as e:
                    logger.error(f"Error in batch {i//batch_size + 1}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    failed_candidates.extend(batch)
                    break
            
            time.sleep(3)
        
        return success_count, failed_candidates

    def retry_failed_candidates(self, failed_candidates):
        if not self.es_available:
            logger.info("Elasticsearch is not available, skipping retry")
            return 0, failed_candidates
            
        success_count = 0
        still_failed = []
        for candidate in failed_candidates:
            if self.index_candidate_from_model(candidate):
                success_count += 1
                logger.info(f"Successfully retried candidate ID {candidate.id}")
            else:
                still_failed.append(candidate)
            time.sleep(3)
        return success_count, still_failed

    def filter_candidates_by_job(self, job_id, limit=10, min_score=0.2, job_info=None):
        """
        Filter candidates that match a specific job using Elasticsearch,
        with improved matching for job titles and skills but reduced boost values.
        """
        if not self.es_available:
            logger.info(f"Elasticsearch is not available, returning empty results for job {job_id}")
            return {"suggested_candidates": []}
            
        try:
            # Get job information
            if job_info:
                job_title = job_info.get('title', '')
                job_description = job_info.get('description', '')
                competence_phare = job_info.get('competence_phare', '')
            else:
                db = SessionLocal()
                try:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if not job:
                        raise ValueError(f"Job with ID {job_id} not found")
                    job_title = job.title if hasattr(job, 'title') and job.title else ""
                    job_description = job.description if hasattr(job, 'description') and job.description else ""
                    competence_phare = job.competence_phare if hasattr(job, 'competence_phare') and job.competence_phare else ""
                    
                    logger.info(f"Job details: ID={job_id}, Title='{job_title}', Competence='{competence_phare}'")
                finally:
                    db.close()

            # Improved term extraction that recognizes common titles vs. domain terms
            def extract_domain_terms(text):
                if not text:
                    return [], []
                    
                # Common job levels/positions to filter out
                common_position_terms = [
                    "senior", "junior", "consultant", "engineer", "manager", "director", 
                    "lead", "chief", "head", "expert", "specialist", "analyste", "analyst", 
                    "développeur", "developer", "architecte", "architect"
                ]
                
                # Split text and convert to lowercase
                words = text.lower().split()
                
                # Separate position terms from domain terms
                position_terms = [w for w in words if w in common_position_terms]
                
                # Extract domain-specific terms (excluding common position terms)
                domain_terms = []
                full_text = text.lower()
                
                # Try to extract multi-word domain terms
                for i in range(len(words)-1):
                    if words[i] == "en" and i < len(words)-1:
                        domain_phrase = " ".join(words[i+1:])
                        domain_terms.append(domain_phrase)
                        break
                
                # If no domain phrases found after "en", extract everything except position terms
                if not domain_terms:
                    domain_terms = [w for w in words if w not in common_position_terms and w not in ["en", "de", "du", "des", "et", "a", "le", "la", "les"]]
                
                # Extract individual domain terms if needed
                if not domain_terms:
                    for w in words:
                        if w not in common_position_terms and w not in ["en", "de", "du", "des", "et", "a", "le", "la", "les"]:
                            domain_terms.append(w)
                
                return position_terms, domain_terms

            # Extract both position and domain terms
            position_terms, domain_terms = extract_domain_terms(job_title)
            
            # Get domain terms from competence_phare too
            _, competence_domain_terms = extract_domain_terms(competence_phare)
            
            # Combine all domain terms
            all_domain_terms = domain_terms + competence_domain_terms
            all_domain_terms = list(set(all_domain_terms))  # Deduplicate
            
            logger.info(f"Position terms: {position_terms}")
            logger.info(f"Domain terms: {all_domain_terms}")

            # Build the improved query that prioritizes domain match over position match
            query = {
                "query": {
                    "bool": {
                        "should": [
                            # 1. Exact match on both domain and position (highest priority)
                            {
                                "match_phrase": {
                                    "job_title": {
                                        "query": job_title,
                                        "boost": 3.0
                                    }
                                }
                            },
                            # 2. Match on domain terms (high priority)
                            {
                                "match": {
                                    "job_title": {
                                        "query": " ".join(all_domain_terms),
                                        "boost": 5.0,
                                        "operator": "or",
                                        "minimum_should_match": "30%"
                                    }
                                }
                            },
                            # 3. Match domain terms in experience
                            {
                                "nested": {
                                    "path": "experiences",
                                    "query": {
                                        "match": {
                                            "experiences.job_title": {
                                                "query": " ".join(all_domain_terms),
                                                "boost": 4.0,
                                                "operator": "or",
                                                "minimum_should_match": "30%"
                                            }
                                        }
                                    },
                                    "score_mode": "max",
                                    "boost": 2.0
                                }
                            },
                            # 4. Match on competence_phare in skills or job title
                            {
                                "multi_match": {
                                    "query": competence_phare,
                                    "fields": ["job_title^1.5", "hard_skills.name^2.0"],
                                    "boost": 2.5,
                                    "type": "best_fields",
                                    "operator": "or",
                                    "minimum_should_match": "30%"
                                }
                            },
                            # 5. Match on hard skills with domain terms
                            {
                                "nested": {
                                    "path": "hard_skills",
                                    "query": {
                                        "terms": {
                                            "hard_skills.name": all_domain_terms,
                                            "boost": 2.0
                                        }
                                    }
                                }
                            },
                            # 6. Lower priority match on position terms only
                            {
                                "match": {
                                    "job_title": {
                                        "query": " ".join(position_terms),
                                        "boost": 0.5,
                                        "operator": "or"
                                    }
                                }
                            },
                            # 7. Match responsibilities with domain terms
                            {
                                "nested": {
                                    "path": "experiences",
                                    "query": {
                                        "match": {
                                            "experiences.responsibilities": {
                                                "query": " ".join(all_domain_terms),
                                                "boost": 1.5
                                            }
                                        }
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1,
                        "must_not": [
                            # Filter out internships and student positions
                            {
                                "match": {
                                    "job_title": {
                                        "query": "stagiaire stage intern étudiant student alternance alternant Élève",
                                        "operator": "or"
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": limit,
                "_source": ["id", "name", "email", "job_title", "hard_skills", "experiences"]
            }

            # Execute the search
            logger.info(f"Elasticsearch query: {query}")
            search_result = self.es.search(
                index=self.index_name,
                body=query
            )

            total_hits = search_result["hits"]["total"]["value"] if "total" in search_result["hits"] else 0
            logger.info(f"Search returned {total_hits} total hits")

            # Process results with improved match reason logic
            candidates = []
            for hit in search_result["hits"]["hits"]:
                source = hit["_source"]
                score = hit["_score"]
                
                # Simple score normalization
                normalized_score = min(max(score / 8, min_score), 1.0)

                # Improved match reason determination
                match_reason = "Correspondance générale avec le profil"
                
                # Check for domain match in current job title
                if source.get("job_title"):
                    job_title_lower = source.get("job_title", "").lower()
                    matching_domain_terms = [term for term in all_domain_terms 
                                            if term.lower() in job_title_lower]
                    
                    if matching_domain_terms:
                        match_reason = f"Domaine similaire: {source.get('job_title')} (termes: {', '.join(matching_domain_terms[:2])})"
                    elif any(term.lower() in job_title_lower for term in position_terms):
                        match_reason = f"Poste similaire: {source.get('job_title')}"
                
                # Check for domain match in skills
                elif source.get("hard_skills"):
                    hard_skills = [skill.get("name", "").lower() for skill in source.get("hard_skills", [])]
                    domain_match = False
                    
                    for term in all_domain_terms:
                        matching_skills = [skill for skill in hard_skills if term.lower() in skill]
                        if matching_skills:
                            match_reason = f"Compétences en {term}: {matching_skills[0]}"
                            domain_match = True
                            break
                    
                    if not domain_match and competence_phare and any(competence_phare.lower() in skill for skill in hard_skills):
                        match_reason = f"Compétence clé: {competence_phare}"
                
                # Check for domain match in experience
                elif "experiences" in source and source["experiences"]:
                    for exp in source["experiences"]:
                        exp_title = exp.get("job_title", "").lower()
                        matching_domain_terms = [term for term in all_domain_terms 
                                            if term.lower() in exp_title]
                        
                        if matching_domain_terms:
                            duration_info = f" (Durée: {exp.get('duration', 'non spécifiée')})" if exp.get("duration") else ""
                            match_reason = f"Expérience en {', '.join(matching_domain_terms[:2])}: {exp.get('job_title')}{duration_info}"
                            break

                candidates.append({
                    "id": source.get("id"),
                    "name": source.get("name", "Candidat sans nom"),
                    "email": source.get("email", "Email non disponible"),
                    "job_title": source.get("job_title", "Poste non spécifié"),
                    "es_score": normalized_score,
                    "match_reason": match_reason,
                    "match_score": score
                })

            if not candidates:
                logger.warning(f"No candidates found for job ID {job_id}")
            else:
                logger.info(f"Found {len(candidates)} candidates for job ID {job_id}")

            return {
                "suggested_candidates": candidates
            }

        except Exception as e:
            import traceback
            logger.error(f"Error filtering candidates for job {job_id}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
