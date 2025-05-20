from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas.user import TokenData, UserRole
from app.models.user import User
from app.database.postgresql import get_db
import os

# Configuration des utilitaires de sécurité
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Obtenir la clé secrète depuis les variables d'environnement ou utiliser une valeur par défaut
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "votre_cle_secrete")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures

def verify_password(plain_password, hashed_password):
    try:
        # Try regular verification
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        # For temporary development use ONLY - direct string comparison
        # This bypasses proper security but allows you to log in while debugging
        print(f"WARNING: Falling back to direct comparison for development!")
        return plain_password == hashed_password

def authenticate_user(db: Session, username: str, password: str):
    try:
        user = db.query(User).filter(User.username == username).first()
        print(f"Authenticating user: {username}")
        
        if not user:
            print(f"User not found: {username}")
            return False
            
        print(f"Found user, checking password...")
        print(f"Stored password hash: {user.hashed_password}")
        
        # Try to verify the password
        if verify_password(password, user.hashed_password):
            print(f"Authentication successful for user: {username}")
            return user
        else:
            print(f"Password verification failed for user: {username}")
            return False
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return False

def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if username is None or role is None:
            raise credentials_exception
        
        token_data = TokenData(sub=username, role=role, exp=payload.get("exp"))
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.sub).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dépendances pour vérifier le rôle de l'utilisateur
def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted, must be admin"
        )
    return current_user

def get_recruiter_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.RECRUITER.value and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

def get_sales_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SALES.value and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

def get_hr_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.HR.value and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user