import sys
import os

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Maintenant vous pouvez importer les modules de app
from models.analysis_cache import AnalysisCache
from database.postgresql import Base, engine

def create_table():
    # Crée la table si elle n'existe pas
    Base.metadata.create_all(bind=engine, tables=[AnalysisCache.__table__])
    print("Table analysis_cache created successfully")

if __name__ == "__main__":
    create_table()