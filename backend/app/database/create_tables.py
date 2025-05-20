# create_tables.py
from postgresql import engine  # Import relatif
import sys
import os

# Ajouter le chemin du répertoire parent pour pouvoir importer Base
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importer Base depuis les modèles de candidats
from app.models.candidate import Base as CandidateBase

# Importer les modèles d'utilisateurs pour s'assurer qu'ils sont enregistrés avec Base
from app.models.user import User, UserActivity

def create_tables():
    # Crée les tables si elles n'existent pas
    CandidateBase.metadata.create_all(bind=engine)
    print("Tables créées/vérifiées avec succès!")

if __name__ == "__main__":
    create_tables()