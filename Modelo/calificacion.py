from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Text
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

class Calificacion(Base):
    __tablename__ = 'Calificaciones'

    ID_Calificacion = Column(Integer, primary_key=True, autoincrement=True)
    ID_Estudiante = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), nullable=False)
    ID_Tarea = Column(Integer, ForeignKey('Tareas.ID_Tarea'), nullable=True)
    ID_Actividad = Column(Integer, nullable=True)
    Puntuacion = Column(DECIMAL(5,2), nullable=True)
    Retroalimentacion = Column(Text, nullable=True)
    FechaCalificacion = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    estudiante = relationship("Usuario", foreign_keys=[ID_Estudiante])
    tarea = relationship("Tarea", foreign_keys=[ID_Tarea])