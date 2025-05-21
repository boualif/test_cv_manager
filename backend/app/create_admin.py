
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.postgresql import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash
from sqlalchemy.exc import IntegrityError

def create_admin_user(username="admin", password="AdminPassword123!", email="admin@example.com"):
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == username).first()
        if existing_admin:
            print(f"User with username '{username}' already exists.")
            return
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role="ADMIN",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user '{username}' created successfully.")
    except IntegrityError:
        db.rollback()
        print(f"Error: User with email '{email}' already exists.")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    # Get credentials from command line arguments or use defaults
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "AdminPassword123!"
    email = sys.argv[3] if len(sys.argv) > 3 else "admin@example.com"
    
    create_admin_user(username, password, email)
