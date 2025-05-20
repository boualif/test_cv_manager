# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from app.database.postgresql import get_db
from app.models.user import User, UserActivity
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.utils.auth import get_password_hash, get_admin_user, get_current_user
from pydantic import ValidationError
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Endpoint pour obtenir les informations de l'utilisateur connecté"""
    return current_user


@router.get("/", response_model=List[UserSchema])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    logger.info(f"Getting users, requested by user ID: {current_user.id}, role: {current_user.role}")
    users = db.query(User).offset(skip).limit(limit).all()
    logger.info(f"Found {len(users)} users")
    return users

@router.post("/", response_model=UserSchema)
def create_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        logger.info(f"Creating user: {user_data.username}")
        
        # Check if username or email already exists
        db_user = db.query(User).filter(User.username == user_data.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        db_email = db.query(User).filter(User.email == user_data.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already in use")
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create new user with string role
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,  # Already validated by Pydantic
            is_active=True
        )
        
        # Save to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Log the activity
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="CREATE_USER",
            description=f"Admin created user {db_user.username}"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"User created: {db_user.username}, ID: {db_user.id}")
        return db_user
    except ValidationError as ve:
        db.rollback()
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(ve)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get dict of data to update
        update_data = user_data.dict(exclude_unset=True)
        
        # Special handling for password if it's being updated
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="UPDATE_USER",
            description=f"Admin updated user {db_user.username}"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"User updated: {db_user.username}, ID: {db_user.id}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Log activity first to prevent foreign key issues
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="DELETE_USER",
            description=f"Admin deleted user {db_user.username}"
        )
        db.add(activity)
        db.commit()
        
        # Now delete the user
        db.delete(db_user)
        db.commit()
        
        logger.info(f"User deleted: {db_user.username}, ID: {db_user.id}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.get("/debug-user/{user_id}", response_model=dict)
def debug_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """Debug endpoint to check user data"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert to dict for debugging
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    logger.info(f"Debug user info: {user_dict}")
    return user_dict