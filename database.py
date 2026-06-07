from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Usamos la DIRECT_URL. 
# ¡OJO!: Borra [YOUR-PASSWORD] (con todo y corchetes) y pon tu contraseña real.
connection_string = "postgresql://postgres.qvxlovckqhmuhfnfhppo:MauricioVisual2026@aws-1-us-west-2.pooler.supabase.com:5432/postgres"

engine = create_engine(connection_string, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()