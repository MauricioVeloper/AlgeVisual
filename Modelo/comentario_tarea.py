from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.dialects.mssql import DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

class ComentarioTarea(Base):
    __tablename__ = 'ComentariosTarea'

    ID_Comentario = Column(Integer, primary_key=True, autoincrement=True)
    ID_Tarea = Column(Integer, ForeignKey('Tareas.ID_Tarea'), nullable=False)
    ID_Usuario = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), nullable=False)
    Contenido = Column(Text, nullable=False)
    Fecha = Column(DateTime, default=datetime.datetime.utcnow)

    # Relación para saber qué maestro escribió el comentario
    autor = relationship("Usuario", foreign_keys=[ID_Usuario])