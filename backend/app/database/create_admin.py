# scripts/create_admin.py
"""
Script to create or update an admin user for testing
Run this script to ensure you have a working admin account for login
"""

import sys
import os
import logging
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import your app modules
from app.database.postgresql import engine, get_db, Base
from models.user import User, UserActivity
from utils.auth import get_password_hash
from sqlalchemy.orm import Session

def create_admin():
    # Create tables if they don't exist
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    # Get DB session
    db = next(get_db())
    
    try:
        # Check if admin exists
        username = "newadmin"
        admin = db.query(User).filter(User.username == username).first()
        
        if admin:
            logger.info(f"Admin user '{username}' already exists (ID: {admin.id})")
            
            # Update admin password
            password = "admin123"  # Change this to a secure password
            admin.hashed_password = get_password_hash(password)
            
            # Make sure user is active and has admin role
            admin.is_active = True
            admin.role = "admin"
            
            # Update modification timestamp
            admin.modified_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Updated password and settings for admin user: {username}")
            
            # Print the admin details
            logger.info(f"Admin Username: {admin.username}")
            logger.info(f"Admin Email: {admin.email}")
            logger.info(f"Admin Role: {admin.role}")
            logger.info(f"Admin Password: {password} (use this to log in)")
            
            # Create activity log for password reset
            activity = UserActivity(
                user_id=admin.id,
                activity_type="RESET_PASSWORD",
                description="Admin password reset via script"
            )
            db.add(activity)
            db.commit()
            
        else:
            # Create new admin user
            logger.info(f"Creating new admin user: '{username}'")
            
            password = "admin123"  # Change this to a secure password
            hashed_password = get_password_hash(password)
            
            # Create admin user
            admin = User(
                username=username,
                email="admin@example.com",
                hashed_password=hashed_password,
                full_name="Admin User",
                role="admin",
                is_active=True,
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow()
            )
            
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            logger.info(f"Admin user created successfully! (ID: {admin.id})")
            
            # Print the admin details
            logger.info(f"Admin Username: {admin.username}")
            logger.info(f"Admin Email: {admin.email}")
            logger.info(f"Admin Role: {admin.role}")
            logger.info(f"Admin Password: {password} (use this to log in)")
            
            # Create activity log
            activity = UserActivity(
                user_id=admin.id,
                activity_type="CREATE_USER",
                description="Admin user created via script"
            )
            db.add(activity)
            db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting admin user creation script...")
    create_admin()
    logger.info("Admin user script completed!")
    print("\n✅ Admin user is ready to use:")
    print("   Username: newadmin")
    print("   Password: admin123")
    print("   Try logging in at: http://localhost:3000/login\n")