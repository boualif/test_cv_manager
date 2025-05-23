from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()  # Remove prefix from here - it's added in main.py

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
    """Handle Zoho OAuth callback"""
    try:
        # For now, just return success message
        # We'll implement token exchange later
        return {
            "message": "Authentication callback received",
            "code": code[:10] + "...",  # Show first 10 chars for debugging
            "status": "callback_received",
            "next_step": "Token exchange will be implemented"
        }
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=400, detail="Authentication callback failed")

@router.get("/connection/status")
async def check_connection_status():
    """Check if Zoho CRM connection is configured"""
    try:
        env_vars = {
            "ZOHO_CLIENT_ID": bool(os.getenv('ZOHO_CLIENT_ID')),
            "ZOHO_CLIENT_SECRET": bool(os.getenv('ZOHO_CLIENT_SECRET')),
            "ZOHO_REDIRECT_URI": bool(os.getenv('ZOHO_REDIRECT_URI')),
            "ZOHO_SCOPE": bool(os.getenv('ZOHO_SCOPE'))
        }
        
        all_configured = all(env_vars.values())
        
        return {
            "connected": False,  # Will be true after full authentication is implemented
            "configured": all_configured,
            "environment_variables": env_vars,
            "status": "configured" if all_configured else "not_configured",
            "client_id_preview": os.getenv('ZOHO_CLIENT_ID', '')[:10] + "..." if os.getenv('ZOHO_CLIENT_ID') else None
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "status": "error"
        }
