from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from .zoho_auth_service import zoho_service

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

class ZohoCRMSync:
    def __init__(self):
        self.service = zoho_service

    async def create_or_update_contact(self, candidate: CandidateData, job_id: str = None):
        """Create or update a contact in Zoho CRM"""
        
        # First, search for existing contact by email
        existing_contact = await self.find_contact_by_email(candidate.email)
        
        contact_data = {
            "First_Name": candidate.first_name,
            "Last_Name": candidate.last_name,
            "Email": candidate.email,
            "Phone": candidate.phone,
            "Experience_Years": candidate.experience_years,
            "Skills": ", ".join(candidate.skills) if candidate.skills else "",
            "Current_Position": candidate.current_position,
            "CV_URL": candidate.cv_url,
            "Match_Score": candidate.match_score,
            "Analysis_Summary": candidate.analysis_summary,
            "Source": "Job Matching App",
            "Last_Updated": datetime.now().isoformat()
        }
        
        if job_id:
            contact_data["Related_Job_ID"] = job_id

        if existing_contact:
            # Update existing contact
            contact_id = existing_contact['id']
            update_data = {"data": [{"id": contact_id, **contact_data}]}
            response = await self.service.make_api_request('PUT', 'Contacts', update_data)
            return {"action": "updated", "contact_id": contact_id, "response": response}
        else:
            # Create new contact
            create_data = {"data": [contact_data]}
            response = await self.service.make_api_request('POST', 'Contacts', create_data)
            contact_id = response['data'][0]['details']['id'] if response.get('data') else None
            return {"action": "created", "contact_id": contact_id, "response": response}

    async def find_contact_by_email(self, email: str):
        """Find contact by email address"""
        try:
            search_params = f"Contacts?criteria=Email:equals:{email}"
            response = await self.service.make_api_request('GET', search_params)
            
            if response.get('data') and len(response['data']) > 0:
                return response['data'][0]
            return None
        except Exception as e:
            print(f"Error searching for contact: {e}")
            return None

    async def create_job_record(self, job: JobData):
        """Create a job record in Zoho CRM (using custom module or Deals)"""
        
        job_data = {
            "Deal_Name": f"Job Opening: {job.title}",
            "Job_Title": job.title,
            "Job_Description": job.description,
            "Requirements": ", ".join(job.requirements),
            "Location": job.location,
            "Salary_Range": job.salary_range,
            "Department": job.department,
            "Job_ID": job.job_id,
            "Stage": "Open",
            "Source": "Job Matching App",
            "Created_Date": datetime.now().isoformat()
        }

        create_data = {"data": [job_data]}
        response = await self.service.make_api_request('POST', 'Deals', create_data)
        
        if response.get('data'):
            return {
                "action": "created",
                "job_record_id": response['data'][0]['details']['id'],
                "response": response
            }
        return {"action": "failed", "response": response}

    async def create_job_application(self, candidate_id: str, job_record_id: str, match_score: float, analysis: str):
        """Create a job application record linking candidate to job"""
        
        application_data = {
            "Subject": "Job Application",
            "Contact_Name": candidate_id,  # This should be the contact ID
            "Related_Deal": job_record_id,  # This should be the deal/job ID
            "Match_Score": match_score,
            "AI_Analysis": analysis,
            "Application_Status": "Applied",
            "Application_Date": datetime.now().isoformat(),
            "Source": "Job Matching App"
        }

        # Create as a Task or custom module record
        create_data = {"data": [application_data]}
        response = await self.service.make_api_request('POST', 'Tasks', create_data)
        
        return {
            "action": "created",
            "application_id": response['data'][0]['details']['id'] if response.get('data') else None,
            "response": response
        }

    async def batch_sync_candidates(self, candidates: List[CandidateData], job_id: str = None):
        """Sync multiple candidates in batch"""
        results = []
        
        for candidate in candidates:
            try:
                result = await self.create_or_update_contact(candidate, job_id)
                results.append({
                    "candidate_email": candidate.email,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "candidate_email": candidate.email,
                    "success": False,
                    "error": str(e)
                })
        
        return results

    async def update_candidate_analysis(self, candidate_email: str, match_score: float, analysis: str):
        """Update candidate with new analysis results"""
        
        contact = await self.find_contact_by_email(candidate_email)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        update_data = {
            "data": [{
                "id": contact['id'],
                "Match_Score": match_score,
                "Analysis_Summary": analysis,
                "Last_Analysis_Date": datetime.now().isoformat()
            }]
        }
        
        response = await self.service.make_api_request('PUT', 'Contacts', update_data)
        return {"updated": True, "response": response}

    async def get_job_candidates(self, job_id: str):
        """Get all candidates for a specific job"""
        try:
            search_params = f"Contacts?criteria=Related_Job_ID:equals:{job_id}"
            response = await self.service.make_api_request('GET', search_params)
            return response.get('data', [])
        except Exception as e:
            print(f"Error fetching job candidates: {e}")
            return []

# Global instance
crm_sync = ZohoCRMSync()
