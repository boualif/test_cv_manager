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

# Add the Elasticsearch startup function
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI application."""
    # Startup
    logger.info("Starting application...")
    
    # Initialize Elasticsearch and create index if needed
    await ensure_elasticsearch_ready()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

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
    allow_origins=["http://localhost:5173"],  # Your frontend origin
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

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(candidate.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(job.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(dashboards.router, prefix="/api/dashboards", tags=["dashboards"])

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
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Seconds
        }
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Unexpected error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during login"
            )
        raise

# Health check endpoint with Elasticsearch status
@app.get("/api/health", tags=["system"])
async def health_check():
    """Health check endpoint with Elasticsearch status"""
    try:
        from app.services.elasticsearch_service import ElasticsearchService
        es_service = ElasticsearchService(host="http://localhost:9200")
        health = es_service.es.cluster.health(request_timeout=5)
        es_status = health['status']
    except:
        es_status = "unavailable"
    
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "elasticsearch": es_status
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_msg = f"Erreur non gérée: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)  # Afficher l'erreur dans la console
    return JSONResponse(
        status_code=500,
        content={"detail": f"Une erreur interne s'est produite: {str(exc)}"})
