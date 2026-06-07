from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Estudiante(Base):
    __tablename__ = 'Estudiantes'

    # La llave primaria es al mismo tiempo la llave foránea que apunta a Usuarios
    ID_Estudiante = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), primary_key=True)

    # Relación bidireccional para acceder fácil a los datos del Usuario (Nombre, Correo, etc.)
    usuario = relationship("Usuario", backref="estudiante_perfil", lazy="joined")

    def __repr__(self):
        return f"<Estudiante ID: {self.ID_Estudiante}>"