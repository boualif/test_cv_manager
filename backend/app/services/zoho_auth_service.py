import os
import requests
import json
from datetime import datetime, timedelta
from fastapi import HTTPException
import asyncio
import aiohttp

class ZohoCRMService:
    def __init__(self):
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
        self.scope = os.getenv('ZOHO_SCOPE')
        self.base_url = "https://www.zohoapis.com/crm/v2"
        self.auth_url = "https://accounts.zoho.com/oauth/v2"
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def get_authorization_url(self):
        """Generate the authorization URL for Zoho OAuth"""
        params = {
            'scope': self.scope,
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'access_type': 'offline'
        }
        
        auth_url = f"{self.auth_url}/auth?"
        auth_url += "&".join([f"{k}={v}" for k, v in params.items()])
        return auth_url

    async def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access and refresh tokens"""
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': authorization_code
            }
            
            async with session.post(f"{self.auth_url}/token", data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    self.refresh_token = token_data['refresh_token']
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    return token_data
                else:
                    raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

    async def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token available")
        
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
            }
            
            async with session.post(f"{self.auth_url}/token", data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    return token_data
                else:
                    raise HTTPException(status_code=400, detail="Failed to refresh token")

    async def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            await self.refresh_access_token()

    async def make_api_request(self, method, endpoint, data=None):
        """Make authenticated API request to Zoho CRM"""
        await self.ensure_valid_token()
        
        headers = {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'POST':
                async with session.post(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)
            elif method.upper() == 'PUT':
                async with session.put(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)

    async def _handle_response(self, response):
        """Handle API response"""
        if response.status in [200, 201]:
            return await response.json()
        elif response.status == 401:
            # Token might be expired, try refreshing
            await self.refresh_access_token()
            raise HTTPException(status_code=401, detail="Token expired, please retry")
        else:
            error_text = await response.text()
            raise HTTPException(status_code=response.status, detail=f"Zoho API error: {error_text}")

# Global instance
zoho_service = ZohoCRMService()
