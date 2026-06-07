from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Docente(Base):
    __tablename__ = 'Docentes'

    # Llave primaria que también es foránea hacia Usuarios
    ID_Docente = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), primary_key=True)
    
    # Campo exclusivo de los maestros
    Descripcion = Column(String(200), nullable=True)

    # Relación para acceder a los datos base (Nombre, Correo, etc.)
    usuario = relationship("Usuario", backref="docente_perfil", lazy="joined")

    def __repr__(self):
        return f"<Docente ID: {self.ID_Docente}>"