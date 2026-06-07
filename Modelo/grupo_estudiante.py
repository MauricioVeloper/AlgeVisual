from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class GrupoEstudiante(Base):
    __tablename__ = 'Grupo_Estudiantes'

    # Llaves primarias compuestas según la estructura de tu base de datos
    ID_Grupo = Column(Integer, ForeignKey('Grupos.ID_Grupo'), primary_key=True, nullable=False)
    ID_Estudiante = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), primary_key=True, nullable=False)
    
    FechaUnion = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones para sacar los datos fácilmente
    grupo = relationship("Grupo", backref="estudiantes_inscritos", lazy="joined")
    usuario = relationship("Usuario", primaryjoin="GrupoEstudiante.ID_Estudiante == Usuario.ID_Usuario", backref="mis_cursos", lazy="joined")