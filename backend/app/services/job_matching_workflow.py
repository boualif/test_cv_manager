import asyncio
from typing import List, Dict, Any
from .zoho_crm_models import crm_sync, CandidateData, JobData
from .job_matching_service import JobMatchingService  # Your existing service
import logging

logger = logging.getLogger(__name__)

class CRMIntegratedJobMatching:
    def __init__(self):
        self.matching_service = JobMatchingService()  # Your existing matching service
        self.crm_sync = crm_sync

    async def process_job_with_crm_sync(
        self, 
        job_description: str, 
        candidates_data: List[Dict[str, Any]],
        sync_to_crm: bool = True
    ):
        """
        Complete workflow: Match candidates to job and sync to CRM
        """
        try:
            # Step 1: Create job record in CRM
            job_data = self.extract_job_data(job_description)
            
            crm_job_result = None
            if sync_to_crm:
                crm_job_result = await self.crm_sync.create_job_record(job_data)
                job_record_id = crm_job_result.get('job_record_id')
                logger.info(f"Created job record in CRM: {job_record_id}")

            # Step 2: Process and match each candidate
            matched_candidates = []
            crm_sync_results = []

            for candidate_info in candidates_data:
                try:
                    # Extract candidate data
                    candidate = self.extract_candidate_data(candidate_info)
                    
                    # Perform matching analysis
                    match_result = await self.matching_service.analyze_candidate_job_match(
                        candidate_info.get('cv_text', ''),
                        job_description
                    )
                    
                    # Update candidate with match results
                    candidate.match_score = match_result.get('match_score', 0)
                    candidate.analysis_summary = match_result.get('analysis_summary', '')
                    
                    matched_candidates.append({
                        'candidate': candidate,
                        'match_result': match_result
                    })
                    
                    # Sync to CRM
                    if sync_to_crm:
                        sync_result = await self.crm_sync.create_or_update_contact(
                            candidate, 
                            job_record_id if crm_job_result else None
                        )
                        
                        # Create job application record
                        if sync_result.get('contact_id') and crm_job_result:
                            await self.crm_sync.create_job_application(
                                sync_result['contact_id'],
                                job_record_id,
                                candidate.match_score,
                                candidate.analysis_summary
                            )
                        
                        crm_sync_results.append(sync_result)
                        logger.info(f"Synced candidate {candidate.email} to CRM")

                except Exception as e:
                    logger.error(f"Error processing candidate {candidate_info.get('email', 'unknown')}: {e}")
                    continue

            # Step 3: Generate summary report
            report = self.generate_matching_report(
                job_data,
                matched_candidates,
                crm_job_result,
                crm_sync_results
            )

            return {
                'job_data': job_data,
                'matched_candidates': matched_candidates,
                'crm_job_record': crm_job_result,
                'crm_sync_results': crm_sync_results,
                'report': report,
                'total_candidates': len(candidates_data),
                'successfully_processed': len(matched_candidates),
                'synced_to_crm': len(crm_sync_results) if sync_to_crm else 0
            }

        except Exception as e:
            logger.error(f"Error in job matching workflow: {e}")
            raise

    def extract_job_data(self, job_description: str) -> JobData:
        """Extract structured job data from job description"""
        # This would use your existing job parsing logic
        # For now, a simplified version:
        
        lines = job_description.split('\n')
        title = lines[0] if lines else "Job Opening"
        
        # Extract requirements (this is simplified - you'd want better parsing)
        requirements = []
        for line in lines:
            if 'requirement' in line.lower() or 'skill' in line.lower():
                requirements.append(line.strip())
        
        return JobData(
            title=title,
            description=job_description,
            requirements=requirements,
            job_id=f"job_{hash(job_description) % 10000}"  # Simple ID generation
        )

    def extract_candidate_data(self, candidate_info: Dict[str, Any]) -> CandidateData:
        """Extract structured candidate data"""
        
        # Parse name
        full_name = candidate_info.get('name', '').split(' ', 1)
        first_name = full_name[0] if full_name else ''
        last_name = full_name[1] if len(full_name) > 1 else ''
        
        # Extract skills from CV text (simplified)
        skills = self.extract_skills_from_cv(candidate_info.get('cv_text', ''))
        
        return CandidateData(
            first_name=first_name,
            last_name=last_name,
            email=candidate_info.get('email', ''),
            phone=candidate_info.get('phone'),
            experience_years=candidate_info.get('experience_years'),
            skills=skills,
            current_position=candidate_info.get('current_position'),
            cv_url=candidate_info.get('cv_url')
        )

    def extract_skills_from_cv(self, cv_text: str) -> List[str]:
        """Extract skills from CV text (simplified version)"""
        # This is a simplified version - you'd want more sophisticated NLP
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'sql', 'postgresql',
            'elasticsearch', 'fastapi', 'docker', 'aws', 'git', 'machine learning',
            'data analysis', 'project management', 'communication', 'leadership'
        ]
        
        cv_lower = cv_text.lower()
        found_skills = [skill for skill in common_skills if skill in cv_lower]
        
        return found_skills

    def generate_
