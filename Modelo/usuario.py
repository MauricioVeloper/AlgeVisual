from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Usuario(Base):
    __tablename__ = 'Usuarios' # Tiene que llamarse exactamente igual que en SQL Server

    ID_Usuario = Column(Integer, primary_key=True, autoincrement=True)
    Matricula = Column(String(50), unique=True, nullable=True)
    NombreCompleto = Column(String(150), nullable=False)
    # Nuevos campos agregados
    Nombres = Column(String(100), nullable=True) 
    ApellidoPaterno = Column(String(50), nullable=True)
    ApellidoMaterno = Column(String(50), nullable=True)
    Correo = Column(String(100), unique=True, nullable=False)
    Contrasena = Column(String(255), nullable=False)
    FotoPerfil = Column(String(255), nullable=True)
    Rol = Column(String(20), nullable=False)
    Estado = Column(Boolean, default=True)

    def _repr_(self):
        return f"<Usuario {self.NombreCompleto} - {self.Rol}>"