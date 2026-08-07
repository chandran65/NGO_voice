import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base, SessionLocal
from app.models import IntentModel, QueryLog
from app.config import INTENTS_REGISTRY

def initialize_database():
    print("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check existing intents
        existing_count = db.query(IntentModel).count()
        if existing_count == 0:
            print("Seeding predefined intent definitions into SQLite...")
            for code, info in INTENTS_REGISTRY.items():
                intent_obj = IntentModel(
                    intent_code=code,
                    name=info["name"],
                    description_en=info["description_en"],
                    description_ta=info["description_ta"],
                    file_name=info["file_name"]
                )
                db.add(intent_obj)
            db.commit()
            print(f"Successfully seeded {len(INTENTS_REGISTRY)} intents!")
        else:
            print(f"Database already contains {existing_count} intents.")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()
