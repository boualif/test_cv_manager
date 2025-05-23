from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
import time
import traceback
import asyncio
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config.settings import settings  # Add this import


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 🚀 NEW: Zoho Auto-Sync Scheduler
class ZohoSyncScheduler:
    def __init__(self):
        self.is_running = False
        self.sync_interval = 300  # 5 minutes
        self.last_sync = None
        
    async def start_auto_sync(self):
        """Start the automatic synchronization scheduler"""
        if self.is_running:
            logger.info("Zoho sync scheduler already running")
            return
            
        self.is_running = True
        logger.info("🚀 Starting Zoho CRM auto-sync scheduler (every 5 minutes)")
        
        # Wait 30 seconds before first sync to let the app fully start
        await asyncio.sleep(30)
        
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
            import aiohttp
            from datetime import datetime
            
            logger.info("🔄 Auto-sync: Checking for new jobs in Zoho CRM...")
            
            async with aiohttp.ClientSession() as session:
                # Call your existing sync endpoint
                async with session.get(
                    "https://test-cv-manager.onrender.com/api/zoho/sync/from-crm?limit=10",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        synced_count = len(result.get('synced_jobs', []))
                        
                        if synced_count > 0:
                            logger.info(f"✅ Auto-sync: {synced_count} new jobs synced from CRM")
                            # Optionally log the job titles
                            for job in result.get('synced_jobs', []):
                                logger.info(f"   - Synced: {job.get('title')}")
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

# Add the Elasticsearch startup function
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Startup
    logger.info("Starting application...")
    
    # Create admin user on startup
    create_admin_user()
    
    # Initialize Elasticsearch and create index if needed
    await ensure_elasticsearch_ready()
    
    # 🚀 NEW: Start Zoho auto-sync if integration is available
    if ZOHO_INTEGRATION_AVAILABLE:
        logger.info("🔄 Starting Zoho CRM auto-synchronization...")
        asyncio.create_task(zoho_scheduler.start_auto_sync())
    else:
        logger.info("Zoho integration not available - skipping auto-sync")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # Stop auto-sync on shutdown
    zoho_scheduler.stop_auto_sync()

# Function to create admin user
def create_admin_user():
    """Create an admin user if it doesn't exist."""
    try:
        from app.database.postgresql import SessionLocal
        from app.models.user import User
        from app.utils.auth import get_password_hash
        from sqlalchemy.exc import IntegrityError
        
        db = SessionLocal()
        try:
            # Check if admin already exists
            admin = db.query(User).filter(User.username == "admin").first()
            if admin:
                logger.info("Admin user already exists")
            else:
                # Create admin user
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("AdminPassword123!"),
                    role="ADMIN",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                logger.info("Admin user created successfully")
        except IntegrityError:
            db.rollback()
            logger.error("Error: User with email 'admin@example.com' already exists")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error importing modules for admin creation: {str(e)}")

async def ensure_elasticsearch_ready():
    """Ensure Elasticsearch is ready and create index if it doesn't exist."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            from app.services.elasticsearch_service import ElasticsearchService
            
            # Use the URL from settings instead of hardcoded localhost
            es_service = ElasticsearchService(host=settings.ELASTICSEARCH_URL)
            
            # Check if index exists
            if not es_service.es.indices.exists(index=es_service.index_name):
                logger.info(f"Index {es_service.index_name} doesn't exist. Creating...")
                if es_service.create_index():
                    logger.info(f"Index {es_service.index_name} created successfully")
                else:
                    logger.error(f"Failed to create index {es_service.index_name}")
            else:
                logger.info(f"Index {es_service.index_name} already exists")
            
            # Check cluster health
            health = es_service.es.cluster.health(request_timeout=10)
            logger.info(f"Elasticsearch cluster health: {health['status']}")
            
            if health['status'] in ['yellow', 'green']:
                logger.info("Elasticsearch is ready for automatic indexing")
                return True
            else:
                logger.warning(f"Elasticsearch health is {health['status']}, but continuing...")
                return True
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Elasticsearch connection failed: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to connect to Elasticsearch after all retries")
                logger.error("Automatic indexing will not work until Elasticsearch is available")
                return False

# Create FastAPI app with lifespan
app = FastAPI(title="Candidate Management API", lifespan=lifespan)

# Configure CORS - this should be at the top
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://test-cv-front.onrender.com"],  # Your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Request to {request.url.path} took {process_time:.4f} seconds")
    return response

# Import dependencies after CORS is configured
from app.database.postgresql import get_db, engine, Base
from app.models.user import User, UserActivity
from app.utils.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.routes import users , candidate ,dashboards,job
from app.models.user import UserActivity

# Import Zoho CRM routes
ZOHO_INTEGRATION_AVAILABLE = False
try:
    from app.routes.zoho_routes import router as zoho_router
    ZOHO_INTEGRATION_AVAILABLE = True
    logger.info("✅ Zoho CRM integration loaded successfully")
except ImportError as e:
    ZOHO_INTEGRATION_AVAILABLE = False
    logger.warning(f"❌ Zoho CRM integration not available: {e}")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(candidate.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(job.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(dashboards.router, prefix="/api/dashboards", tags=["dashboards"])

# Include Zoho CRM router if available
if ZOHO_INTEGRATION_AVAILABLE:
    app.include_router(zoho_router, prefix="/api/zoho", tags=["zoho-crm"])
    logger.info("✅ Zoho CRM routes registered successfully")

# 🚀 NEW: Zoho Sync Control Endpoints
@app.get("/api/zoho/sync/auto/status", tags=["zoho-sync"])
async def get_auto_sync_status():
    """Get the status of automatic Zoho synchronization"""
    if not ZOHO_INTEGRATION_AVAILABLE:
        return {"error": "Zoho integration not available"}
    
    return {
        "is_running": zoho_scheduler.is_running,
        "last_sync": zoho_scheduler.last_sync.isoformat() if zoho_scheduler.last_sync else None,
        "sync_interval_seconds": zoho_scheduler.sync_interval,
        "sync_interval_minutes": zoho_scheduler.sync_interval // 60,
        "zoho_integration_available": ZOHO_INTEGRATION_AVAILABLE
    }

@app.post("/api/zoho/sync/auto/restart", tags=["zoho-sync"])
async def restart_auto_sync():
    """Restart the automatic Zoho synchronization"""
    if not ZOHO_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=400, detail="Zoho integration not available")
    
    # Stop current sync
    zoho_scheduler.stop_auto_sync()
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Start new sync
    asyncio.create_task(zoho_scheduler.start_auto_sync())
    
    return {
        "success": True,
        "message": "Zoho auto-sync restarted successfully"
    }

@app.post("/api/zoho/sync/manual", tags=["zoho-sync"])
async def trigger_manual_sync():
    """Trigger a manual synchronization immediately"""
    if not ZOHO_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=400, detail="Zoho integration not available")
    
    logger.info("🔄 Manual sync triggered by user")
    result = await zoho_scheduler.perform_sync()
    
    if result:
        return {
            "success": True,
            "message": "Manual sync completed",
            "result": result
        }
    else:
        return {
            "success": False,
            "message": "Manual sync failed",
            "error": "Check logs for details"
        }

# Root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Candidate Management API",
        "version": "1.0.0", 
        "status": "online",
        "docs_url": "/docs",
        "zoho_integration": ZOHO_INTEGRATION_AVAILABLE,
        "zoho_auto_sync": zoho_scheduler.is_running if ZOHO_INTEGRATION_AVAILABLE else False
    }

# Auth endpoint for session creation
@app.post("/api/auth/token", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        # Authenticate user
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Log successful login
        activity = UserActivity(
            user_id=user.id,
            activity_type="LOGIN",
            description=f"User logged in successfully"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"User {user.username} (ID: {user.id}) logged in successfully")
        
        # Return token with user information
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Seconds
            "zoho_integration": ZOHO_INTEGRATION_AVAILABLE,
            "zoho_auto_sync_running": zoho_scheduler.is_running if ZOHO_INTEGRATION_AVAILABLE else False
        }
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Unexpected error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during login"
            )
        raise

# Special endpoint to create admin user (can be removed after use)
@app.post("/api/admin/init", tags=["admin"])
async def init_admin():
    """Initialize admin user - one-time use endpoint."""
    try:
        create_admin_user()
        return {"message": "Admin user creation initiated"}
    except Exception as e:
        logger.error(f"Error in init_admin endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin creation failed: {str(e)}"
        )

# Health check endpoint with Elasticsearch and Zoho status
@app.get("/api/health", tags=["system"])
async def health_check():
    """Health check endpoint with Elasticsearch and Zoho CRM status"""
    try:
        from app.services.elasticsearch_service import ElasticsearchService
        
        # Use the URL from settings instead of hardcoded localhost
        es_service = ElasticsearchService(host=settings.ELASTICSEARCH_URL)
        health = es_service.es.cluster.health(request_timeout=5)
        es_status = health['status']
    except:
        es_status = "unavailable"
    
    # Check Zoho CRM connection status
    zoho_status = "not_configured"
    if ZOHO_INTEGRATION_AVAILABLE:
        try:
            from app.services.zoho_auth_service import zoho_service
            # Try to check if we have valid tokens
            if zoho_service.access_token:
                zoho_status = "connected"
            else:
                zoho_status = "not_authenticated"
        except:
            zoho_status = "error"
    
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "elasticsearch": es_status,
        "zoho_crm": zoho_status,
        "zoho_auto_sync": {
            "running": zoho_scheduler.is_running if ZOHO_INTEGRATION_AVAILABLE else False,
            "last_sync": zoho_scheduler.last_sync.isoformat() if zoho_scheduler.last_sync else None
        },
        "integrations": {
            "zoho_available": ZOHO_INTEGRATION_AVAILABLE
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_msg = f"Erreur non gérée: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)  # Afficher l'erreur dans la console
    return JSONResponse(
        status_code=500,
        content={"detail": f"Une erreur interne s'est produite: {str(exc)}"})
