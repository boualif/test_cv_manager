from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import RedirectResponse
from typing import List, Optional
import logging
from .zoho_auth_service import zoho_service
from .zoho_crm_models import crm_sync, CandidateData, JobData

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/zoho", tags=["Zoho CRM Integration"])

@router.get("/auth/login")
async def initiate_zoho_auth():
    """Initiate Zoho OAuth flow"""
    try:
        auth_url = zoho_service.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error initiating Zoho auth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate authentication")

@router.get("/auth/callback")
async def zoho_auth_callback(code: str = Query(...)):
    """Handle Zoho OAuth callback"""
    try:
        token_data = await zoho_service.exchange_code_for_tokens(code)
        
        # Store tokens securely (you might want to save to database)
        # For now, they're stored in the service instance
        
        return {
            "message": "Authentication successful",
            "status": "connected",
            "expires_in": token_data.get('expires_in')
        }
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

@router.post("/candidates/sync")
async def sync_candidates(
    candidates: List[CandidateData],
    job_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Sync candidates to Zoho CRM"""
    try:
        if background_tasks:
            # Process in background for large batches
            background_tasks.add_task(
                process_candidate_sync,
                candidates,
                job_id
            )
            return {
                "message": f"Syncing {len(candidates)} candidates in background",
                "status": "processing"
            }
        else:
            # Process immediately for small batches
            results = await crm_sync.batch_sync_candidates(candidates, job_id)
            
            success_count = sum(1 for r in results if r['success'])
            error_count = len(results) - success_count
            
            return {
                "message": "Candidate sync completed",
                "total_processed": len(results),
                "successful": success_count,
                "errors": error_count,
                "results": results
            }
    except Exception as e:
        logger.error(f"Error syncing candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync candidates: {str(e)}")

@router.post("/jobs/create")
async def create_job_in_crm(job: JobData):
    """Create a job record in Zoho CRM"""
    try:
        result = await crm_sync.create_job_record(job)
        
        if result['action'] == 'created':
            return {
                "message": "Job created successfully in CRM",
                "job_record_id": result['job_record_id'],
                "zoho_response": result['response']
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create job record")
            
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.post("/candidates/{candidate_email}/analysis")
async def update_candidate_analysis(
    candidate_email: str,
    match_score: float,
    analysis: str
):
    """Update candidate with new match analysis"""
    try:
        result = await crm_sync.update_candidate_analysis(
            candidate_email,
            match_score,
            analysis
        )
        
        return {
            "message": "Candidate analysis updated successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error updating candidate analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update analysis: {str(e)}")

@router.post("/jobs/{job_id}/applications")
async def create_job_application(
    job_id: str,
    candidate_email: str,
    match_score: float,
    analysis: str
):
    """Create a job application record linking candidate to job"""
    try:
        # First find the candidate
        contact = await crm_sync.find_contact_by_email(candidate_email)
        if not contact:
            raise HTTPException(status_code=404, detail="Candidate not found in CRM")
        
        # Create application record
        result = await crm_sync.create_job_application(
            contact['id'],
            job_id,
            match_score,
            analysis
        )
        
        return {
            "message": "Job application created successfully",
            "application_id": result['application_id']
        }
    except Exception as e:
        logger.error(f"Error creating job application: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")

@router.get("/jobs/{job_id}/candidates")
async def get_job_candidates(job_id: str):
    """Get all candidates for a specific job"""
    try:
        candidates = await crm_sync.get_job_candidates(job_id)
        
        return {
            "job_id": job_id,
            "candidate_count": len(candidates),
            "candidates": candidates
        }
    except Exception as e:
        logger.error(f"Error fetching job candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch candidates: {str(e)}")

@router.get("/connection/status")
async def check_connection_status():
    """Check if Zoho CRM connection is active"""
    try:
        # Try to make a simple API call to test connection
        response = await zoho_service.make_api_request('GET', 'users?type=CurrentUser')
        
        return {
            "connected": True,
            "user_info": response.get('users', [{}])[0] if response.get('users') else {},
            "status": "active"
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "status": "disconnected"
        }

# Background task function
async def process_candidate_sync(candidates: List[CandidateData], job_id: Optional[str] = None):
    """Background task to process candidate sync"""
    try:
        results = await crm_sync.batch_sync_candidates(candidates, job_id)
        
        # Log results
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        
        logger.info(f"Background sync completed: {success_count} successful, {error_count} errors")
        
        # You could also store results in database or send notification
        
    except Exception as e:
        logger.error(f"Background sync failed: {e}")

# Webhook endpoint for real-time sync
@router.post("/webhook/job-match")
async def job_match_webhook(
    candidate_email: str,
    job_id: str,
    match_score: float,
    analysis: str,
    candidate_data: Optional[CandidateData] = None
):
    """Webhook to automatically sync when a job match is found"""
    try:
        # If candidate data is provided, sync to CRM first
        if candidate_data:
            await crm_sync.create_or_update_contact(candidate_data, job_id)
        
        # Update analysis
        await crm_sync.update_candidate_analysis(candidate_email, match_score, analysis)
        
        # Create application record
        contact = await crm_sync.find_contact_by_email(candidate_email)
        if contact:
            await crm_sync.create_job_application(
                contact['id'],
                job_id,
                match_score,
                analysis
            )
        
        return {
            "message": "Job match processed successfully",
            "candidate_email": candidate_email,
            "job_id": job_id,
            "match_score": match_score
        }
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
