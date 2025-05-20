# app/utils/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import TokenData
from app.models.user import User
from app.database.postgresql import get_db
import os
import logging

# Configure logging with more detailed info
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auth.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security utilities configuration
# Use a more flexible context that can handle different hash formats
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fix the tokenUrl path to match your actual endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Get secret key from environment or use a default (but warn)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "INSECURE_DEFAULT_SECRET_KEY_PLEASE_CHANGE"
    logger.warning("Using default JWT_SECRET_KEY. This is insecure! Set it in your environment.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def verify_password(plain_password, hashed_password):
    """Verify password against hash with better error handling and debugging"""
    try:
        logger.debug(f"Verifying password (length: {len(plain_password)})")
        # Check if hashed_password is in a valid format
        if not hashed_password or len(hashed_password) < 20:  # Sanity check on hash length
            logger.error(f"Invalid hash format (length: {len(hashed_password) if hashed_password else 0})")
            return False
            
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        # For debugging only - print more details about the hash
        logger.debug(f"Hash format: {hashed_password[:10]}... (total length: {len(hashed_password)})")
        return False

def get_password_hash(password):
    """Generate password hash with additional validation"""
    if not password or len(password) < 4:
        logger.warning(f"Attempted to hash weak password (length: {len(password) if password else 0})")
    
    hashed = pwd_context.hash(password)
    logger.debug(f"Generated password hash (length: {len(hashed)})")
    return hashed

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with improved debugging and error handling"""
    try:
        logger.info(f"Authentication attempt for user: '{username}'")
        
        # Debug DB session
        if not db:
            logger.error("Database session is None")
            return False
            
        # Query user with debug info
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found")
            return False
        
        logger.debug(f"User found: ID={user.id}, Role={user.role}, Active={user.is_active}")
        
        # Debug password verification
        logger.debug(f"Hashed password from DB: {user.hashed_password[:10]}... (length: {len(user.hashed_password)})")
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            return False
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User '{username}' is inactive")
            return False
            
        logger.info(f"Authentication successful for user: '{username}'")
        return user
    except Exception as e:
        logger.error(f"Error during authentication: {str(e)}", exc_info=True)
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token with improved error handling"""
    try:
        to_encode = data.copy()
        logger.debug(f"Creating token with data: {to_encode}")
        
        # Set expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        # Create JWT token
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Token created successfully (length: {len(encoded_jwt)})")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authentication token"
        )

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token with improved validation"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.debug(f"Validating token (length: {len(token)})")
        
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        logger.debug(f"Token payload: username={username}, role={role}")
        
        if username is None or role is None:
            logger.warning("Token validation failed: missing username or role")
            raise credentials_exception
        
        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token validation failed: missing expiration")
            raise credentials_exception
            
        # Convert exp to datetime for comparison
        exp_datetime = datetime.fromtimestamp(exp)
        now = datetime.utcnow()
        
        if now > exp_datetime:
            logger.warning(f"Token validation failed: token expired for user '{username}'")
            logger.debug(f"Token expired at {exp_datetime}, current time is {now}")
            raise credentials_exception
            
        token_data = TokenData(sub=username, role=role, exp=exp)
    except JWTError as e:
        logger.error(f"JWT token error: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.username == token_data.sub).first()
    if user is None:
        logger.warning(f"Token validation failed: user '{token_data.sub}' not found")
        raise credentials_exception
        
    if not user.is_active:
        logger.warning(f"Token validation failed: user '{user.username}' is inactive")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        
    logger.debug(f"User validated successfully: {user.username} (ID: {user.id})")
    return user

# Rest of the role-based functions remain the same
def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        logger.warning(f"Permission denied: user '{current_user.username}' (role: {current_user.role}) attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted, must be admin"
        )
    return current_user

def get_recruiter_user(current_user: User = Depends(get_current_user)):
    # Instead of checking for specific roles, allow all roles
    # This effectively allows any authenticated user to access recruiter endpoints
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    logger.info(f"CV upload access granted to user '{current_user.username}' (role: {current_user.role})")
    return current_user

def get_sales_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "sales" and current_user.role != "admin":
        logger.warning(f"Permission denied: user '{current_user.username}' (role: {current_user.role}) attempted sales access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions, must be sales or admin"
        )
    return current_user

def get_hr_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "hr" and current_user.role != "admin":
        logger.warning(f"Permission denied: user '{current_user.username}' (role: {current_user.role}) attempted HR access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions, must be HR or admin"
        )
    return current_user


def get_cv_upload_user(current_user: User = Depends(get_current_user)):
    """
    Allow any authenticated and active user to upload CVs,
    regardless of their role.
    """
    # Simply check if the user is active
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Log access
    logger.info(f"CV upload access granted to user '{current_user.username}' (role: {current_user.role})")
    return current_user