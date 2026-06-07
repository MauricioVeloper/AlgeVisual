from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.dialects.mssql import DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

class Actividad(Base):
    __tablename__ = 'Actividades'
    ID_Actividad = Column(Integer, primary_key=True, autoincrement=True)
    ID_Grupo = Column(Integer, ForeignKey('Grupos.ID_Grupo'), nullable=False)
    Titulo = Column(String(150), nullable=False)
    Tipo = Column(String(50), default='Examen')
    TiempoMinutos = Column(Integer, nullable=False)
    FechaPublicacion = Column(DateTime, default=datetime.datetime.utcnow)
    FechaLimite = Column(DateTime, nullable=True)
    Estado = Column(Boolean, default=True)
    preguntas = relationship("PreguntaExamen", backref="actividad", cascade="all, delete-orphan")
    grupo = relationship("Grupo", backref="actividades_creadas") # <--- SOLUCIÓN AL ERROR

class PreguntaExamen(Base):
    __tablename__ = 'PreguntasExamen'
    ID_Pregunta = Column(Integer, primary_key=True, autoincrement=True)
    ID_Actividad = Column(Integer, ForeignKey('Actividades.ID_Actividad'), nullable=False)
    TextoPregunta = Column(Text, nullable=False)
    
    opciones = relationship("OpcionPregunta", backref="pregunta", cascade="all, delete-orphan")

class OpcionPregunta(Base):
    __tablename__ = 'OpcionesPregunta'
    ID_Opcion = Column(Integer, primary_key=True, autoincrement=True)
    ID_Pregunta = Column(Integer, ForeignKey('PreguntasExamen.ID_Pregunta'), nullable=False)
    TextoOpcion = Column(Text, nullable=False)
    EsCorrecta = Column(Boolean, default=False)