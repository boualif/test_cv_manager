from fastapi import APIRouter, HTTPException, Query, Depends  # ← Ajout de Depends
from fastapi.responses import RedirectResponse
from typing import List, Optional
import logging
import os
import aiohttp
import json
from datetime import datetime, timedelta

# Import du service d'authentification
from app.services.zoho_auth_service import zoho_service

# IMPORTS MANQUANTS AJOUTÉS :
from sqlalchemy.orm import Session
from app.database.postgresql import get_db
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Stockage persistant amélioré des tokens
TOKEN_STORAGE = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": None,
    "last_updated": None
}

async def ensure_valid_token():
    """Assurer qu'on a un token valide, avec refresh automatique"""
    try:
        # Vérifier si on a un token
        if not TOKEN_STORAGE["access_token"]:
            logger.warning("❌ No access token available")
            return None
        
        # Vérifier si le token a expiré
        if TOKEN_STORAGE["expires_at"]:
            expires_at = datetime.fromisoformat(TOKEN_STORAGE["expires_at"])
            # Refresh 5 minutes avant expiration
            if datetime.now() >= (expires_at - timedelta(minutes=5)):
                logger.info("🔄 Token expires soon, attempting refresh...")
                success = await refresh_stored_token()
                if not success:
                    logger.error("❌ Failed to refresh token")
                    return None
        
        return TOKEN_STORAGE["access_token"]
        
    except Exception as e:
        logger.error(f"Error ensuring valid token: {e}")
        return None

async def refresh_stored_token():
    """Rafraîchir le token stocké"""
    try:
        if not TOKEN_STORAGE["refresh_token"]:
            logger.error("❌ No refresh token available")
            return False
        
        # Utiliser le service d'authentification existant
        zoho_service.refresh_token = TOKEN_STORAGE["refresh_token"]
        await zoho_service.refresh_access_token()
        
        # Mettre à jour le stockage
        TOKEN_STORAGE["access_token"] = zoho_service.access_token
        TOKEN_STORAGE["refresh_token"] = zoho_service.refresh_token
        TOKEN_STORAGE["expires_at"] = zoho_service.token_expires_at.isoformat() if zoho_service.token_expires_at else None
        TOKEN_STORAGE["last_updated"] = datetime.now().isoformat()
        
        logger.info("✅ Token refreshed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {e}")
        return False

async def make_zoho_api_request_persistent(method: str, endpoint: str, data: dict = None):
    """Version améliorée avec gestion automatique des tokens"""
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            # Assurer qu'on a un token valide
            token = await ensure_valid_token()
            if not token:
                if attempt == 0:
                    logger.warning("🔄 No valid token, attempting refresh...")
                    await refresh_stored_token()
                    continue
                else:
                    raise HTTPException(
                        status_code=401, 
                        detail="Zoho authentication required. Please re-authenticate via /api/zoho/auth/login"
                    )
            
            headers = {
                'Authorization': f'Zoho-oauthtoken {token}',
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
                        
        except HTTPException as e:
            if e.status_code == 401 and attempt == 0:
                logger.warning("🔄 Token expired during request, invalidating and retrying...")
                # Invalider le token actuel et retry
                TOKEN_STORAGE["access_token"] = None
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Request failed: {e}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
            continue
    
    raise HTTPException(status_code=500, detail="Max retries exceeded")

async def handle_zoho_response(response):
    """Handle Zoho API response"""
    if response.status in [200, 201]:
        return await response.json()
    elif response.status == 401:
        # Token expiré - sera géré par la logique de retry
        raise HTTPException(status_code=401, detail="Token expired")
    else:
        error_text = await response.text()
        logger.error(f"❌ Zoho API error: {response.status} - {error_text}")
        raise HTTPException(status_code=response.status, detail=f"Zoho API error: {error_text}")

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
            "has_access_token": bool(TOKEN_STORAGE["access_token"]),
            "token_expires_at": TOKEN_STORAGE.get("expires_at"),
            "last_updated": TOKEN_STORAGE.get("last_updated")
        }
    }

@router.get("/auth/login")
async def initiate_zoho_auth():
    """Initiate Zoho OAuth flow"""
    try:
        auth_url = zoho_service.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error initiating Zoho auth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate authentication: {str(e)}")

@router.get("/auth/callback")
async def zoho_auth_callback(code: str = Query(...)):
    """Handle Zoho OAuth callback with persistent storage"""
    try:
        # Utiliser le service d'authentification existant
        token_data = await zoho_service.exchange_code_for_tokens(code)
        
        # Stocker dans le système persistant
        TOKEN_STORAGE["access_token"] = zoho_service.access_token
        TOKEN_STORAGE["refresh_token"] = zoho_service.refresh_token
        TOKEN_STORAGE["expires_at"] = zoho_service.token_expires_at.isoformat() if zoho_service.token_expires_at else None
        TOKEN_STORAGE["last_updated"] = datetime.now().isoformat()
        
        logger.info("✅ Zoho authentication successful with persistent storage")
        
        # Redirect to frontend with success
        return RedirectResponse(
            url="https://test-cv-front.onrender.com?zoho_auth=success",
            status_code=302
        )
    except Exception as e:
        logger.error(f"❌ Error in OAuth callback: {e}")
        return RedirectResponse(
            url="https://test-cv-front.onrender.com?zoho_auth=error",
            status_code=302
        )

@router.get("/connection/status")
async def check_connection_status():
    """Check if Zoho CRM connection is active with persistent token management"""
    try:
        token = await ensure_valid_token()
        
        if not token:
            return {
                "connected": False,
                "status": "not_authenticated",
                "message": "No valid token available. Please authenticate.",
                "auth_url": "/api/zoho/auth/login"
            }
        
        # Tester la connexion
        response = await make_zoho_api_request_persistent('GET', 'users?type=CurrentUser')
        user_info = response.get('users', [{}])[0] if response.get('users') else {}
        
        return {
            "connected": True,
            "status": "active",
            "user_info": {
                "name": user_info.get('full_name'),
                "email": user_info.get('email'),
                "role": user_info.get('role', {}).get('name')
            },
            "token_expires_at": TOKEN_STORAGE.get("expires_at"),
            "last_updated": TOKEN_STORAGE.get("last_updated")
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "status": "error",
            "auth_url": "/api/zoho/auth/login"
        }

@router.post("/contacts/create")
async def create_contact(contact_data: dict):
    """Create a new contact in Zoho CRM with persistent authentication"""
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
        response = await make_zoho_api_request_persistent('POST', 'Contacts', create_data)
        
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
    """Search for contacts by email with persistent authentication"""
    try:
        response = await make_zoho_api_request_persistent('GET', f'Contacts/search?criteria=Email:equals:{email}')
        
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
    """Create a job record in Zoho CRM with persistent authentication"""
    try:
        # Format job data for Zoho avec mapping amélioré
        zoho_job = {
            "Deal_Name": f"Job Opening: {job_data.get('title', 'Untitled')}",
            "Job_Title": job_data.get('title', ''),
            "Job_Description": job_data.get('description', ''),
            "Requirements": ', '.join(job_data.get('requirements', [])) if job_data.get('requirements') else job_data.get('competence_phare', ''),
            "Location": job_data.get('location', 'Tunisia'),
            "Salary_Range": job_data.get('salary_range', ''),
            "Department": job_data.get('department', 'Engineering'),
            "Job_ID": job_data.get('job_id', f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "Job_Type": job_data.get('job_type_etiquette', 'technique'),
            "Stage": "Open",
            "Source": "Job Matching App",
            "Created_Date": datetime.now().isoformat()
        }
        
        # Remove empty values
        zoho_job = {k: v for k, v in zoho_job.items() if v is not None and v != ''}
        
        create_data = {"data": [zoho_job]}
        response = await make_zoho_api_request_persistent('POST', 'Deals', create_data)
        
        if response.get('data') and len(response['data']) > 0:
            job_id = response['data'][0]['details']['id']
            return {
                "success": True,
                "message": "Job created successfully in Zoho CRM",
                "job_id": job_id,
                "zoho_response": response
            }
        else:
            return {
                "success": False,
                "message": "Failed to create job in Zoho CRM",
                "zoho_response": response
            }
            
    except Exception as e:
        logger.error(f"❌ Error creating job in Zoho: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.post("/jobs/sync-from-app")
async def sync_job_from_app(job_data: dict):
    """Synchroniser un job depuis votre app vers Zoho CRM avec le bon mapping"""
    try:
        # Mapping adapté à votre structure d'app
        zoho_job = {
            "Deal_Name": f"Job Opening: {job_data.get('title', 'Sans titre')}",
            "Job_Title": job_data.get('title', ''),
            "Job_Description": job_data.get('description', ''),
            "Requirements": job_data.get('competence_phare', ''),  # Compétence principale
            "Job_Type": job_data.get('job_type_etiquette', ''),    # technique/commercial
            "Stage": "Open",
            "Source": "Job Matching App",
            "Created_Date": datetime.now().isoformat(),
            "App_Job_ID": str(job_data.get('id', ''))  # ID de votre app
        }
        
        # Nettoyer les valeurs vides
        zoho_job = {k: v for k, v in zoho_job.items() if v is not None and v != ''}
        
        create_data = {"data": [zoho_job]}
        response = await make_zoho_api_request_persistent('POST', 'Deals', create_data)
        
        if response.get('data') and len(response['data']) > 0:
            zoho_job_id = response['data'][0]['details']['id']
            return {
                "success": True,
                "message": f"Job '{job_data.get('title')}' synchronisé avec succès",
                "zoho_job_id": zoho_job_id,
                "app_job_id": job_data.get('id'),
                "zoho_response": response
            }
        else:
            return {
                "success": False,
                "message": "Échec de la synchronisation",
                "zoho_response": response
            }
            
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de synchronisation: {str(e)}")

@router.post("/jobs/sync-existing/{job_id}")
async def sync_existing_job(job_id: int):
    """Synchroniser un job existant de votre app vers Zoho"""
    try:
        # Récupérer le job depuis votre API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://test-cv-manager.onrender.com/api/jobs/{job_id}") as response:
                if response.status == 200:
                    job_data = await response.json()
                    
                    # Synchroniser avec le bon mapping
                    sync_result = await sync_job_from_app(job_data)
                    return sync_result
                else:
                    raise HTTPException(status_code=404, detail=f"Job {job_id} non trouvé dans votre app")
                    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
@router.get("/sync/from-crm")
async def sync_jobs_from_crm(
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Nombre maximum de jobs à synchroniser")
):
    """Synchronisation manuelle: récupérer les jobs depuis Zoho CRM"""
    try:
        # Récupérer les deals récents depuis Zoho
        response = await make_zoho_api_request_persistent(
            'GET', 
            f'Deals?fields=id,Deal_Name,Job_Title,Job_Description,Requirements,Job_Type,Location,Department,Salary_Range,Source,Created_Time&per_page={limit}&sort_order=desc&sort_by=Created_Time'
        )
        
        deals = response.get('data', [])
        synced_jobs = []
        
        for deal in deals:
            try:
                # Ignorer les jobs créés par notre app (pour éviter les boucles)
                if deal.get('Source') == 'Job Matching App':
                    continue
                
                # Extraire le titre du job
                title = deal.get('Job_Title') or deal.get('Deal_Name', '').replace('Job Opening: ', '')
                
                # Vérifier si le job existe déjà dans notre app
                existing_job = db.query(Job).filter(Job.title == title).first()
                if existing_job:
                    continue
                
                # Trouver un utilisateur admin pour créer le job
                admin_user = db.query(User).filter(User.role == "ADMIN").first()
                if not admin_user:
                    logger.error("❌ No admin user found")
                    continue
                
                # Créer le nouveau job dans notre app
                new_job = Job(
                    title=title,
                    description=deal.get('Job_Description', ''),
                    competence_phare=deal.get('Requirements', ''),
                    job_type_etiquette=deal.get('Job_Type', 'technique'),
                    created_by_id=admin_user.id
                )
                
                db.add(new_job)
                db.commit()
                db.refresh(new_job)
                
                synced_jobs.append({
                    "app_job_id": new_job.id,
                    "title": new_job.title,
                    "zoho_deal_id": deal.get('id')
                })
                
                logger.info(f"✅ Synced job '{new_job.title}' from CRM")
                
            except Exception as e:
                logger.error(f"❌ Error syncing deal {deal.get('id')}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Synchronized {len(synced_jobs)} jobs from Zoho CRM",
            "synced_jobs": synced_jobs,
            "total_deals_found": len(deals)
        }
        
    except Exception as e:
        logger.error(f"❌ CRM sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"CRM sync failed: {str(e)}")
@router.get("/jobs/test-sync/{job_id}")
async def test_sync_job(job_id: int):
    """Tester la synchronisation d'un job sans l'envoyer à Zoho"""
    try:
        # Récupérer le job depuis votre API
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://test-cv-manager.onrender.com/api/jobs/{job_id}") as response:
                if response.status == 200:
                    job_data = await response.json()
                    
                    # Montrer le mapping sans envoyer
                    zoho_job = {
                        "Deal_Name": f"Job Opening: {job_data.get('title', 'Sans titre')}",
                        "Job_Title": job_data.get('title', ''),
                        "Job_Description": job_data.get('description', ''),
                        "Requirements": job_data.get('competence_phare', ''),
                        "Job_Type": job_data.get('job_type_etiquette', ''),
                        "Stage": "Open",
                        "Source": "Job Matching App",
                        "Created_Date": datetime.now().isoformat(),
                        "App_Job_ID": str(job_data.get('id', ''))
                    }
                    
                    return {
                        "success": True,
                        "message": "Aperçu du mapping (non envoyé à Zoho)",
                        "original_job": job_data,
                        "zoho_mapping": zoho_job
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"Job {job_id} non trouvé")
                    
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
