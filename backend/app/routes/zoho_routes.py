from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import List, Optional
import logging
import os
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple token storage (in production, use database)
access_token = None
refresh_token = None
token_expires_at = None

@router.get("/test")
async def test_zoho():
    """Test endpoint to verify Zoho integration is working"""
    return {
        "message": "Zoho routes loaded successfully",
        "env_check": {
            "client_id_exists": bool(os.getenv('ZOHO_CLIENT_ID')),
            "client_secret_exists": bool(os.getenv('ZOHO_CLIENT_SECRET')),
            "redirect_uri": os.getenv('ZOHO_REDIRECT_URI'),
            "scope": os.getenv('ZOHO_SCOPE')
        },
        "auth_status": {
            "has_access_token": bool(access_token),
            "token_expires_at": token_expires_at.isoformat() if token_expires_at else None
        }
    }

@router.get("/auth/login")
async def initiate_zoho_auth():
    """Initiate Zoho OAuth flow"""
    try:
        client_id = os.getenv('ZOHO_CLIENT_ID')
        redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
        scope = os.getenv('ZOHO_SCOPE')
        
        if not all([client_id, redirect_uri, scope]):
            missing_vars = []
            if not client_id:
                missing_vars.append('ZOHO_CLIENT_ID')
            if not redirect_uri:
                missing_vars.append('ZOHO_REDIRECT_URI')
            if not scope:
                missing_vars.append('ZOHO_SCOPE')
            
            raise HTTPException(
                status_code=500, 
                detail=f"Missing environment variables: {', '.join(missing_vars)}"
            )
        
        # Generate auth URL
        auth_url = f"https://accounts.zoho.com/oauth/v2/auth?scope={scope}&client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&access_type=offline"
        
        return {"auth_url": auth_url}
        
    except Exception as e:
        logger.error(f"Error initiating Zoho auth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate authentication: {str(e)}")

@router.get("/auth/callback")
async def zoho_auth_callback(code: str = Query(...)):
    """Handle Zoho OAuth callback and exchange code for tokens"""
    global access_token, refresh_token, token_expires_at
    
    try:
        client_id = os.getenv('ZOHO_CLIENT_ID')
        client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
        
        # Exchange code for tokens
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'code': code
            }
            
            async with session.post('https://accounts.zoho.com/oauth/v2/token', data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data['access_token']
                    refresh_token = token_data.get('refresh_token')
                    expires_in = token_data.get('expires_in', 3600)
                    token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info("Successfully obtained Zoho access token")
                    
                    # Redirect to frontend with success
                    return RedirectResponse(
                        url="https://test-cv-front.onrender.com?zoho_auth=success",
                        status_code=302
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {error_text}")
                    return RedirectResponse(
                        url="https://test-cv-front.onrender.com?zoho_auth=error",
                        status_code=302
                    )
                    
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return RedirectResponse(
            url="https://test-cv-front.onrender.com?zoho_auth=error",
            status_code=302
        )

async def make_zoho_api_request(method: str, endpoint: str, data: dict = None):
    """Make authenticated API request to Zoho CRM"""
    global access_token
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated with Zoho CRM")
    
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    
    url = f"https://www.zohoapis.com/crm/v2/{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        if method.upper() == 'GET':
            async with session.get(url, headers=headers) as response:
                return await handle_zoho_response(response)
        elif method.upper() == 'POST':
            async with session.post(url, headers=headers, json=data) as response:
                return await handle_zoho_response(response)
        elif method.upper() == 'PUT':
            async with session.put(url, headers=headers, json=data) as response:
                return await handle_zoho_response(response)

async def handle_zoho_response(response):
    """Handle Zoho API response"""
    if response.status in [200, 201]:
        return await response.json()
    else:
        error_text = await response.text()
        logger.error(f"Zoho API error: {response.status} - {error_text}")
        raise HTTPException(status_code=response.status, detail=f"Zoho API error: {error_text}")

@router.get("/connection/status")
async def check_connection_status():
    """Check if Zoho CRM connection is active"""
    try:
        if not access_token:
            return {
                "connected": False,
                "status": "not_authenticated",
                "message": "No access token available"
            }
        
        # Try to make a simple API call to test connection
        response = await make_zoho_api_request('GET', 'users?type=CurrentUser')
        
        user_info = response.get('users', [{}])[0] if response.get('users') else {}
        
        return {
            "connected": True,
            "status": "active",
            "user_info": {
                "name": user_info.get('full_name'),
                "email": user_info.get('email'),
                "role": user_info.get('role', {}).get('name')
            },
            "token_expires_at": token_expires_at.isoformat() if token_expires_at else None
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "status": "error"
        }

@router.post("/contacts/create")
async def create_contact(contact_data: dict):
    """Create a new contact in Zoho CRM"""
    try:
        # Format contact data for Zoho
        zoho_contact = {
            "First_Name": contact_data.get('first_name', ''),
            "Last_Name": contact_data.get('last_name', ''),
            "Email": contact_data.get('email', ''),
            "Phone": contact_data.get('phone', ''),
            "Experience_Years": contact_data.get('experience_years'),
            "Skills": ', '.join(contact_data.get('skills', [])),
            "Current_Position": contact_data.get('current_position', ''),
            "CV_URL": contact_data.get('cv_url', ''),
            "Match_Score": contact_data.get('match_score'),
            "Analysis_Summary": contact_data.get('analysis_summary', ''),
            "Source": "Job Matching App",
            "Last_Updated": datetime.now().isoformat()
        }
        
        # Remove empty values
        zoho_contact = {k: v for k, v in zoho_contact.items() if v is not None and v != ''}
        
        create_data = {"data": [zoho_contact]}
        response = await make_zoho_api_request('POST', 'Contacts', create_data)
        
        if response.get('data') and len(response['data']) > 0:
            contact_id = response['data'][0]['details']['id']
            return {
                "success": True,
                "message": "Contact created successfully",
                "contact_id": contact_id,
                "zoho_response": response
            }
        else:
            return {
                "success": False,
                "message": "Failed to create contact",
                "zoho_response": response
            }
            
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")

@router.get("/contacts/search")
async def search_contacts(email: str = Query(...)):
    """Search for contacts by email"""
    try:
        response = await make_zoho_api_request('GET', f'Contacts/search?criteria=Email:equals:{email}')
        
        contacts = response.get('data', [])
        
        return {
            "found": len(contacts) > 0,
            "count": len(contacts),
            "contacts": contacts
        }
        
    except Exception as e:
        logger.error(f"Error searching contacts: {e}")
        return {
            "found": False,
            "count": 0,
            "contacts": [],
            "error": str(e)
        }

@router.post("/jobs/create")
async def create_job(job_data: dict):
    """Create a job record in Zoho CRM (as a Deal)"""
    try:
        # Format job data for Zoho
        zoho_job = {
            "Deal_Name": f"Job Opening: {job_data.get('title', 'Untitled')}",
            "Job_Title": job_data.get('title', ''),
            "Job_Description": job_data.get('description', ''),
            "Requirements": ', '.join(job_data.get('requirements', [])),
            "Location": job_data.get('location', ''),
            "Salary_Range": job_data.get('salary_range', ''),
            "Department": job_data.get('department', ''),
            "Job_ID": job_data.get('job_id', f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "Stage": "Open",
            "Source": "Job Matching App",
            "Created_Date": datetime.now().isoformat()
        }
        
        # Remove empty values
        zoho_job = {k: v for k, v in zoho_job.items() if v is not None and v != ''}
        
        create_data = {"data": [zoho_job]}
        response = await make_zoho_api_request('POST', 'Deals', create_data)
        
        if response.get('data') and len(response['data']) > 0:
            job_id = response['data'][0]['details']['id']
            return {
                "success": True,
                "message": "Job created successfully",
                "job_id": job_id,
                "zoho_response": response
            }
        else:
            return {
                "success": False,
                "message": "Failed to create job",
                "zoho_response": response
            }
            
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")
