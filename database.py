from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Usamos el nombre exacto de tu computadora y servidor
username = 'sa'
password = '12345' # Pon tu contraseña real aquí
server = r'127.0.1,1433' # Asegúrate de usar la IP correcta y el puerto si es necesario
database = 'AlgeVisual'

# 2. Cambiamos el driver a 'SQL Server' y agregamos TrustServerCertificate=yes
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=SQL+Server&TrustServerCertificate=yes"

engine = create_engine(connection_string, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()