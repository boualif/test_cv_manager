import json
import logging
import traceback
from typing import List, Dict, Any
from openai import OpenAI
from app.config.settings import settings
from requests import Session
from app.services.elasticsearch_service import ElasticsearchService
from app.services.analysis_cache_service import AnalysisCacheService
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobMatcher:
    """Class to handle job-candidate matching without relying on the API endpoint"""
    
    def __init__(self, openai_api_key=None):
        """Initialize with API key"""
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY 
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Check your settings.py file or provide it directly.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def get_prompt_template(self, job_type: str, cv_content: str = "") -> str:
        """Return the complete prompt for GPT to analyze candidate-job fit"""

        system_instruction = (
            "Tu es un expert en recrutement technique spécialisé dans l'évaluation des candidats pour des postes en informatique. "
            "Ta mission est d'analyser l'adéquation entre un profil de candidat et les exigences d'un poste, "
            "puis de fournir une évaluation structurée sous forme JSON."
        )

        base_instruction = """
        Pour évaluer l'adéquation entre un candidat et un poste, suis ce cadre d'analyse en 4 étapes:

        Étape 1: Analyse des exigences du poste
        - Identifie les années d'expérience requises
        - Liste les compétences techniques spécifiques demandées
        - Note l'expertise sectorielle/domaine nécessaire
        - Identifie les soft skills requis

        Étape 2: Analyse du profil du candidat
        - Calcule l'expérience professionnelle pertinente totale
        - Catalogue les compétences techniques du candidat
        - Note toute expertise sectorielle/domaine
        - Examine l'éducation et les certifications

        Étape 3: Analyse des écarts
        - Compare l'expérience requise vs l'expérience réelle
        - Confronte les compétences techniques requises vs les compétences du candidat
        - Évalue l'adéquation des connaissances du domaine
        - Évalue l'alignement des soft skills

        Étape 4: Évaluation finale
        - Fournis un score pour les compétences techniques (sur 100) basé sur la correspondance des compétences. Réduis ce score si des compétences clés sont manquantes (par exemple, -10 par compétence manquante).
        - Fournis un score pour l'expérience (sur 100) basé sur l'adéquation de l'expérience. Réduis ce score si l'expérience est insuffisante (par exemple, -10 par année manquante).
        - Fournis un score pour les autres facteurs (sur 100) basé sur l'adéquation de la localisation, des certifications, et autres critères. Réduis ce score si la localisation ne correspond pas ou si d'autres écarts significatifs existent.
        - Résume les principales forces et faiblesses
        - Fais une recommandation finale sur l'adéquation au poste
        - Assure-toi que les scores reflètent précisément les écarts identifiés. Par exemple, si le candidat manque plusieurs compétences clés ou années d'expérience, les scores doivent être significativement plus bas.
        """

        format_json = """
        {
          "job_analysis": {
            "required_experience": "X années",
            "key_technical_skills": ["Compétence 1", "Compétence 2", "..."],
            "domain_expertise": ["Domaine 1", "Domaine 2", "..."],
            "soft_skills": ["Soft skill 1", "Soft skill 2", "..."]
          },
          "candidate_profile": {
            "total_relevant_experience": "X années",
            "technical_skills": ["Compétence 1", "Compétence 2", "..."],
            "domain_expertise": ["Domaine 1", "Domaine 2", "..."],
            "education_certifications": ["Formation/Certification 1", "Formation/Certification 2", "..."]
          },
          "gap_analysis": {
            "experience_comparison": {
              "required": "X années",
              "actual": "Y années",
              "matching_experience": ["Expérience 1", "Expérience 2", "..."],
              "experience_gaps": ["Écart 1", "Écart 2", "..."]
            },
            "technical_skills": {
              "matching_skills": ["Compétence 1", "Compétence 2", "..."],
              "missing_skills": ["Compétence 1", "Compétence 2", "..."]
            },
            "domain_knowledge": {
              "fit_assessment": "Évaluation de l'adéquation",
              "strengths": ["Force 1", "Force 2", "..."],
              "gaps": ["Écart 1", "Écart 2", "..."]
            },
            "soft_skills": {
              "alignment": "Évaluation de l'alignement",
              "strengths": ["Force 1", "Force 2", "..."],
              "areas_for_development": ["Domaine 1", "Domaine 2", "..."]
            }
          },
          "final_assessment": {
            "skills_score": "X",
            "experience_score": "Y",
            "other_score": "Z",
            "key_strengths": ["Force 1", "Force 2", "..."],
            "significant_gaps": ["Écart 1", "Écart 2", "..."],
            "fit_recommendation": "Recommandation sur l'adéquation au poste",
            "candidate_name": "Nom du candidat",
            "years_of_experience": "X années",
            "location": "Localisation",
            "email": "Email",
            "phone": "Téléphone"
          }
        }
        """

        full_prompt = f"""
        {system_instruction}

        Tu dois analyser l'adéquation entre le profil d'un candidat et un poste de type "{job_type}".
        Utilise le cadre d'analyse en 4 étapes fourni et retourne tes résultats au format JSON spécifié.

        CV du candidat :
        \"\"\"
        {cv_content}
        \"\"\"

        Cadre d'analyse à suivre :
        {base_instruction}

        Format de réponse :
        Ta réponse doit être UNIQUEMENT un objet JSON valide respectant cette structure :
        {format_json}

        IMPORTANT: Ne génère aucun texte avant ou après le JSON. Ta réponse doit uniquement contenir l'objet JSON valide.
        """
        return full_prompt

    def validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure and content of an analysis, adjusting scores if necessary"""
        logger.info("Validating analysis structure and content...")
        main_sections = ["job_analysis", "candidate_profile", "gap_analysis", "final_assessment"]
        for section in main_sections:
            if section not in analysis:
                logger.error(f"Missing main section: {section}")
                return {"valid": False, "analysis": analysis}
        
        required_scores = ["skills_score", "experience_score", "other_score"]
        for score in required_scores:
            if score not in analysis["final_assessment"]:
                logger.error(f"Missing {score} in final_assessment")
                return {"valid": False, "analysis": analysis}
            try:
                score_value = float(analysis["final_assessment"][score])
                if not 0 <= score_value <= 100:
                    logger.error(f"{score} out of range (0-100): {score_value}")
                    return {"valid": False, "analysis": analysis}
            except (ValueError, TypeError):
                logger.error(f"Invalid {score} format: {analysis['final_assessment'][score]}")
                return {"valid": False, "analysis": analysis}
        
        required_candidate_info = ["candidate_name", "years_of_experience", "location"]
        for info in required_candidate_info:
            if info not in analysis["final_assessment"]:
                logger.error(f"Missing {info} in final_assessment")
                return {"valid": False, "analysis": analysis}
        
        # Adjust scores based on gaps
        skills_score = float(analysis["final_assessment"]["skills_score"])
        experience_score = float(analysis["final_assessment"]["experience_score"])
        other_score = float(analysis["final_assessment"]["other_score"])
        
        # Reduce skills_score if there are missing skills
        missing_skills = analysis["gap_analysis"]["technical_skills"]["missing_skills"]
        if missing_skills and len(missing_skills) > 0:
            reduction = min(len(missing_skills) * 10, 50)  # Reduce by 10% per missing skill, max 50%
            adjusted_skills_score = max(skills_score - reduction, 0)
            logger.info(f"Adjusting skills_score from {skills_score} to {adjusted_skills_score} due to {len(missing_skills)} missing skills")
            analysis["final_assessment"]["skills_score"] = str(adjusted_skills_score)
        
        # Reduce experience_score if there are experience gaps
        experience_gaps = analysis["gap_analysis"]["experience_comparison"]["experience_gaps"]
        if experience_gaps and len(experience_gaps) > 0:
            try:
                required_years = float(analysis["gap_analysis"]["experience_comparison"]["required"].split()[0])
                actual_years = float(analysis["gap_analysis"]["experience_comparison"]["actual"].split()[0])
                years_missing = required_years - actual_years
                if years_missing > 0:
                    reduction = min(years_missing * 10, 50)  # Reduce by 10% per missing year, max 50%
                    adjusted_experience_score = max(experience_score - reduction, 0)
                    logger.info(f"Adjusting experience_score from {experience_score} to {adjusted_experience_score} due to {years_missing} years missing")
                    analysis["final_assessment"]["experience_score"] = str(adjusted_experience_score)
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse experience years for adjustment: {str(e)}")
        
        # Reduce other_score if there are significant gaps
        significant_gaps = analysis["final_assessment"]["significant_gaps"]
        if significant_gaps and len(significant_gaps) > 0:
            reduction = min(len(significant_gaps) * 10, 30)  # Reduce by 10% per gap, max 30%
            adjusted_other_score = max(other_score - reduction, 0)
            logger.info(f"Adjusting other_score from {other_score} to {adjusted_other_score} due to {len(significant_gaps)} significant gaps")
            analysis["final_assessment"]["other_score"] = str(adjusted_other_score)
        
        logger.info("Analysis structure and content validation successful")
        return {"valid": True, "analysis": analysis}

    def extract_score(self, score_value: str) -> float:
        """Extract numerical score as a float from a string or number"""
        try:
            if isinstance(score_value, (int, float)):
                score = float(score_value)
            else:
                score_str = str(score_value).strip()
                if '/' in score_str:
                    score = float(score_str.split('/')[0].strip())
                elif '%' in score_str:
                    score = float(score_str.replace('%', '').strip())
                else:
                    score = float(score_str)
            
            # Ensure score is between 0 and 100
            if score > 100:
                logger.warning(f"Score {score} exceeds 100, capping at 100")
                score = 100.0
            elif score < 0:
                logger.warning(f"Score {score} is negative, setting to 0")
                score = 0.0
            
            return score / 100.0  # Convert to 0-1 range for calculations
        except (ValueError, AttributeError, IndexError) as e:
            logger.error(f"Error extracting score from {score_value}: {str(e)}")
            return 0.0

    def determine_match_quality(self, combined_score: float) -> str:
        """Determine the match quality based on the combined score"""
        score_percent = combined_score * 100
        if score_percent >= 85:
            return "Excellent"
        elif score_percent >= 70:
            return "Très bon"
        elif score_percent >= 60:
            return "Bon"
        elif score_percent >= 50:
            return "Moyen"
        else:
            return "Faible"

    def calculate_combined_score(self, skills_score: float, experience_score: float, other_score: float) -> float:
        """Calculate the combined score using weighted factors"""
        weights = {"skills": 0.4, "experience": 0.4, "other": 0.2}
        combined = (
            (skills_score * weights["skills"]) +
            (experience_score * weights["experience"]) +
            (other_score * weights["other"])
        )
        return round(combined * 100)  # Return as percentage

    def analyze_candidate(self, job_info: Dict[str, Any], candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single candidate against a job using GPT"""
        try:
            job_title = job_info.get("title", "")
            job_description = job_info.get("description", "Non spécifiée")
            competence_phare = job_info.get("competence_phare", "Non spécifiée")
            job_type = job_info.get("job_type_etiquette", "technique")
            
            candidate_id = candidate_data.get("id")
            candidate_name = candidate_data.get("name", "Unknown")
            candidate_email = candidate_data.get("email", "Non spécifié")
            resume_data = candidate_data.get("resume_json", {})
            
            if isinstance(resume_data, str):
                try:
                    resume_data = json.loads(resume_data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON format for candidate {candidate_id}")
                    return {
                        "candidate_id": candidate_id,
                        "error": "Format JSON invalide pour le CV",
                        "status": "failed"
                    }
            
            resume_data_str = json.dumps(resume_data, indent=2)
            
            system_prompt = (
                "Vous êtes un expert en recrutement technique spécialisé dans l'évaluation des profils IT. "
                "Votre tâche est d'analyser la correspondance entre un CV et une offre d'emploi, "
                "puis de fournir une évaluation structurée qui met en évidence les forces et les écarts du candidat."
            )
            
            complete_prompt = self.get_prompt_template(job_type, resume_data_str)
            user_prompt = f"""
            DESCRIPTION DU POSTE:
            Titre: {job_title}
            Description: {job_description}
            Compétences clés: {competence_phare}
            Type de Poste: {job_type}
            
            Évaluez l'adéquation entre ce candidat et cette offre d'emploi en utilisant le cadre d'analyse en 4 étapes.
            Retournez UNIQUEMENT un JSON valide sans aucun texte avant ou après.
            """
            
            logger.info(f"Calling OpenAI API for candidate {candidate_id}")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + complete_prompt}
                ],
                max_tokens=2500,
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Raw GPT response for candidate {candidate_id}: {response_text}")
            
            if not response_text:
                logger.error(f"Empty response from OpenAI for candidate {candidate_id}")
                return {
                    "candidate_id": candidate_id,
                    "error": "L'API OpenAI a retourné une réponse vide",
                    "status": "failed"
                }
            
            try:
                analysis = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response for candidate {candidate_id}: {str(e)}")
                return {
                    "candidate_id": candidate_id,
                    "error": f"OpenAI a retourné un JSON non valide: {str(e)}",
                    "status": "failed"
                }
            
            validation_result = self.validate_analysis(analysis)
            if not validation_result["valid"]:
                logger.error(f"Invalid analysis structure for candidate {candidate_id}")
                return {
                    "candidate_id": candidate_id,
                    "error": "Structure d'analyse non valide",
                    "status": "failed"
                }
            
            analysis = validation_result["analysis"]
            
            # Extract scores after validation adjustments
            skills_score = self.extract_score(analysis["final_assessment"]["skills_score"])
            experience_score = self.extract_score(analysis["final_assessment"]["experience_score"])
            other_score = self.extract_score(analysis["final_assessment"]["other_score"])
            
            logger.info(f"Scores for candidate {candidate_id}: skills={skills_score*100}%, experience={experience_score*100}%, other={other_score*100}%")
            
            # Calculate combined score
            combined_score = self.calculate_combined_score(skills_score, experience_score, other_score)
            combined_score_str = f"{combined_score}%"
            
            logger.info(f"Combined score for candidate {candidate_id}: {combined_score_str}")
            
            cv_analysis = {
                "skills_score": f"{int(skills_score * 100)}%",
                "job_title_and_experience_score": f"{int(experience_score * 100)}%",
                "other_score": f"{int(other_score * 100)}%",
                "combined_score": combined_score_str,
                "skills_gaps": analysis["gap_analysis"]["technical_skills"]["missing_skills"],
                "job_title_and_experience_gaps": analysis["gap_analysis"]["experience_comparison"].get("experience_gaps", []),
                "other_gaps": analysis["final_assessment"]["significant_gaps"],
                "skills_match": analysis["gap_analysis"]["technical_skills"]["matching_skills"],
                "job_title_and_experience_match": analysis["gap_analysis"]["experience_comparison"].get("matching_experience", []),
                "candidate_name": analysis["final_assessment"]["candidate_name"],
                "general_strengths": analysis["final_assessment"]["key_strengths"],
                "general_weaknesses": analysis["final_assessment"]["significant_gaps"],
                "estimated_age": "Non spécifié",
                "location": analysis["final_assessment"]["location"],
                "years_of_experience": analysis["final_assessment"]["years_of_experience"],
                "email": analysis["final_assessment"].get("email", candidate_email),
                "phone": analysis["final_assessment"].get("phone", "Non spécifié")
            }
            
            return {
                "id": candidate_id,
                "candidate_id": candidate_id,
                "name": candidate_name,
                "email": candidate_email,
                "cv_analysis": cv_analysis,
                "combined_score": combined_score_str,
                "match_quality": self.determine_match_quality(combined_score / 100.0),
                "status": "success",
                "detailed_analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing candidate {candidate_data.get('id')}: {str(e)}")
            return {
                "candidate_id": candidate_data.get("id"),
                "error": str(e),
                "status": "failed"
            }

def analyze_candidate_cv_with_job(job_id: int, candidate_ids: List[int], current_user: User, db: Session) -> Dict[str, Any]:
    """
    Analyze candidates' CVs against a job offer.
    If candidate_ids contains "auto", use Elasticsearch to find the best candidates.
    """
    try:
        from app.models.candidate import Candidate, Resume
        from app.models.job import Job

        logger.info(f"Starting analysis for job_id: {job_id}, candidates: {candidate_ids}")

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

        es_service = ElasticsearchService()
        es_candidates_map = {}

        if not candidate_ids or (len(candidate_ids) == 1 and str(candidate_ids[0]).lower() == "auto"):
            logger.info("Auto mode: Using Elasticsearch to find best matching candidates")
            es_result = es_service.filter_candidates_by_job(job_id, min_score=0.1, limit=5, job_info=job_info)
            
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
                    "message": "No matching candidates found by Elasticsearch"
                }
            
            es_candidates = es_result.get("suggested_candidates", [])
            candidate_ids = []
            for c in es_candidates:
                candidate_id = int(c["id"])
                candidate_ids.append(candidate_id)
                es_candidates_map[candidate_id] = {
                    "match_reason": c.get("match_reason", "Correspondance par Elasticsearch")
                }
            logger.info(f"Elasticsearch found {len(candidate_ids)} candidates: {candidate_ids}")
        else:
            for candidate_id in candidate_ids:
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
                                "match_reason": c.get("match_reason", "Correspondance par Elasticsearch")
                            }
                            break
                if int(candidate_id) not in es_candidates_map:
                    es_candidates_map[int(candidate_id)] = {
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

                cached_analysis = cache_service.get_cached_analysis(job_id, candidate_id)
                if cached_analysis:
                    logger.info(f"Using cached analysis for candidate {candidate_id}")
                    logger.info(f"Cached raw analysis for candidate {candidate_id}: {cached_analysis}")
                    # Recompute combined_score from cached cv_analysis scores
                    skills_score = matcher.extract_score(cached_analysis["cv_analysis"]["skills_score"])
                    experience_score = matcher.extract_score(cached_analysis["cv_analysis"]["job_title_and_experience_score"])
                    other_score = matcher.extract_score(cached_analysis["cv_analysis"]["other_score"])
                    combined_score = matcher.calculate_combined_score(skills_score, experience_score, other_score)
                    cached_analysis["combined_score"] = f"{combined_score}%"
                    logger.info(f"Recomputed combined score for candidate {candidate_id}: {cached_analysis['combined_score']}")
                    gpt_result = cached_analysis
                else:
                    logger.info(f"No cached analysis found for candidate {candidate_id}, performing new analysis")
                    gpt_result = matcher.analyze_candidate(job_info, candidate_data)
                    cache_service.cache_analysis(
                        job_id=job_id,
                        candidate_id=candidate_id,
                        job_title=job.title,
                        candidate_name=candidate.name,
                        analysis=gpt_result
                    )
                    logger.info(f"New combined score for candidate {candidate_id}: {gpt_result.get('combined_score', 'N/A')} after caching")

                if gpt_result["status"] != "success":
                    analysis_results.append(gpt_result)
                    continue

                match_reason = es_candidates_map.get(int(candidate_id), {"match_reason": "Non évalué"})["match_reason"]
                gpt_result["es_match_reason"] = match_reason

                if str(candidate_ids[0]).lower() == "auto":
                    gpt_result["source"] = "elasticsearch_suggestion"

                analysis_results.append(gpt_result)
                logger.info(f"Analysis completed for candidate {candidate_id} with combined score {gpt_result['combined_score']}")

            except Exception as e:
                logger.error(f"Error processing candidate {candidate_id}: {str(e)}")
                analysis_results.append({
                    "candidate_id": candidate_id,
                    "error": str(e),
                    "status": "failed"
                })

        successful_results = [r for r in analysis_results if r.get("status") == "success"]
        failed_results = [r for r in analysis_results if r.get("status") != "success"]
        sorted_successful = sorted(
            successful_results,
            key=lambda x: int(x.get("combined_score", "0%").replace("%", "")),
            reverse=True
        )
        sorted_results = sorted_successful + failed_results

        # Log all combined scores for verification
        combined_scores = [
            f"Candidate {r['candidate_id']}: {r.get('combined_score', 'N/A')}"
            for r in sorted_results
        ]
        logger.info(f"Completed analysis for {len(analysis_results)} candidates with combined scores: {', '.join(combined_scores)}")

        return {
            "job_info": {
                "job_id": job.id,
                "job_title": job.title,
                "competence_phare": job_info["competence_phare"],
                "job_type": job_info["job_type_etiquette"]
            },
            "total_candidates_analyzed": len(analysis_results),
            "analyses": sorted_results,
            "search_method": "auto" if str(candidate_ids[0]).lower() == "auto" else "manual",
            "score_methodology": "Combined: 40% Skills + 40% Experience + 20% Other Factors"
        }

    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Analysis failed: {str(e)}")