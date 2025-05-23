# app/services/zoho_sync_scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
from sqlalchemy.orm import Session
from app.database.postgresql import SessionLocal
from app.models.job import Job
from app.models.user import User

logger = logging.getLogger(__name__)

class ZohoSyncScheduler:
    def __init__(self):
        self.is_running = False
        self.sync_interval = 100  # 5 minutes
        self.last_sync = None
        
    async def start_auto_sync(self):
        """Start the automatic synchronization scheduler"""
        if self.is_running:
            logger.info("Sync scheduler already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting Zoho CRM auto-sync scheduler")
        
        while self.is_running:
            try:
                await self.perform_sync()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"❌ Auto-sync error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def stop_auto_sync(self):
        """Stop the automatic synchronization"""
        self.is_running = False
        logger.info("🛑 Stopping Zoho CRM auto-sync scheduler")
    
    async def perform_sync(self):
        """Perform the actual synchronization"""
        try:
            logger.info("🔄 Starting automatic sync from Zoho CRM")
            
            async with aiohttp.ClientSession() as session:
                # Call your existing sync endpoint
                async with session.get(
                    "https://test-cv-manager.onrender.com/api/zoho/sync/from-crm?limit=20",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        synced_count = len(result.get('synced_jobs', []))
                        
                        if synced_count > 0:
                            logger.info(f"✅ Auto-sync: {synced_count} new jobs synced from CRM")
                        else:
                            logger.info("ℹ️ Auto-sync: No new jobs to sync")
                            
                        self.last_sync = datetime.now()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Auto-sync failed: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Auto-sync error: {e}")
            return None

# Global scheduler instance
zoho_scheduler = ZohoSyncScheduler()

# Add these endpoints to your zoho_routes.py

@router.post("/sync/auto/start")
async def start_auto_sync():
    """Start automatic synchronization from Zoho CRM"""
    try:
        # Start the scheduler in the background
        asyncio.create_task(zoho_scheduler.start_auto_sync())
        
        return {
            "success": True,
            "message": "Automatic sync started",
            "sync_interval": f"{zoho_scheduler.sync_interval} seconds"
        }
    except Exception as e:
        logger.error(f"Failed to start auto-sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start auto-sync: {str(e)}")

@router.post("/sync/auto/stop")
async def stop_auto_sync():
    """Stop automatic synchronization"""
    zoho_scheduler.stop_auto_sync()
    return {
        "success": True,
        "message": "Automatic sync stopped"
    }

@router.get("/sync/auto/status")
async def get_auto_sync_status():
    """Get the status of automatic synchronization"""
    return {
        "is_running": zoho_scheduler.is_running,
        "last_sync": zoho_scheduler.last_sync.isoformat() if zoho_scheduler.last_sync else None,
        "sync_interval_seconds": zoho_scheduler.sync_interval,
        "next_sync_estimate": (
            zoho_scheduler.last_sync + timedelta(seconds=zoho_scheduler.sync_interval)
        ).isoformat() if zoho_scheduler.last_sync else "Unknown"
    }

# IMPROVED sync/from-crm endpoint with better error handling
@router.get("/sync/from-crm-improved")
async def sync_jobs_from_crm_improved(
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of jobs to sync"),
    force: bool = Query(False, description="Force sync even if job exists")
):
    """IMPROVED: Sync jobs from Zoho CRM with better error handling"""
    try:
        logger.info(f"🔄 Starting improved CRM sync (limit={limit}, force={force})")
        
        # Get deals from Zoho with basic fields first
        response = await make_zoho_api_request_persistent(
            'GET', 
            f'Deals?fields=id,Deal_Name,Description,Stage,Created_Time,Modified_Time&per_page={limit}&sort_order=desc&sort_by=Modified_Time'
        )
        
        if not response or not response.get('data'):
            logger.warning("No data received from Zoho CRM")
            return {
                "success": False,
                "message": "No data received from Zoho CRM",
                "synced_jobs": [],
                "total_deals_found": 0
            }
        
        deals = response.get('data', [])
        synced_jobs = []
        skipped_jobs = []
        errors = []
        
        # Get admin user once
        admin_user = db.query(User).filter(User.role == "ADMIN").first()
        if not admin_user:
            admin_user = db.query(User).first()  # Fallback to any user
            
        if not admin_user:
            raise HTTPException(status_code=500, detail="No users found in database")
        
        for deal in deals:
            try:
                deal_id = deal.get('id')
                deal_name = deal.get('Deal_Name', '')
                
                # Extract job title from deal name
                if deal_name.startswith('Job Opening: '):
                    title = deal_name.replace('Job Opening: ', '').strip()
                elif deal_name:
                    title = deal_name.strip()
                else:
                    title = f"Job from CRM {deal_id}"
                
                # Check if job already exists
                if not force:
                    existing_job = db.query(Job).filter(Job.title == title).first()
                    if existing_job:
                        skipped_jobs.append({
                            "title": title,
                            "reason": "Job already exists",
                            "existing_job_id": existing_job.id
                        })
                        continue
                
                # Create new job
                new_job = Job(
                    title=title,
                    description=deal.get('Description', ''),
                    competence_phare="From CRM",  # Default value
                    job_type_etiquette="technique",  # Default value
                    created_by_id=admin_user.id
                )
                
                db.add(new_job)
                db.commit()
                db.refresh(new_job)
                
                synced_jobs.append({
                    "app_job_id": new_job.id,
                    "title": new_job.title,
                    "zoho_deal_id": deal_id,
                    "created_at": new_job.created_at.isoformat()
                })
                
                logger.info(f"✅ Synced: '{title}' (ID: {new_job.id})")
                
            except Exception as e:
                error_msg = f"Error syncing deal {deal.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                db.rollback()
                continue
        
        # Summary
        total_processed = len(synced_jobs) + len(skipped_jobs) + len(errors)
        
        logger.info(f"✅ Sync complete: {len(synced_jobs)} synced, {len(skipped_jobs)} skipped, {len(errors)} errors")
        
        return {
            "success": True,
            "message": f"Sync completed: {len(synced_jobs)} new jobs imported",
            "synced_jobs": synced_jobs,
            "skipped_jobs": skipped_jobs,
            "errors": errors,
            "total_deals_found": len(deals),
            "total_processed": total_processed,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ CRM sync failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"CRM sync failed: {str(e)}")

# Webhook endpoint for real-time sync (if Zoho supports it)
@router.post("/webhook/deal-created")
async def handle_zoho_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Handle Zoho CRM webhook for real-time sync"""
    try:
        logger.info("📥 Received Zoho webhook")
        
        # Extract deal information from webhook
        deal_data = webhook_data.get('data', {})
        
        if not deal_data:
            return {"status": "ignored", "reason": "No deal data"}
        
        # Trigger immediate sync for this specific deal
        result = await sync_jobs_from_crm_improved(db=db, limit=1, force=False)
        
        return {
            "status": "processed",
            "webhook_data": webhook_data,
            "sync_result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}
