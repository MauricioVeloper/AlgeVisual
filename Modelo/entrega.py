from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

class Entrega(Base):
    __tablename__ = 'Entregas'

    ID_Entrega = Column(Integer, primary_key=True, autoincrement=True)
    ID_Tarea = Column(Integer, ForeignKey('Tareas.ID_Tarea'), nullable=False)
    ID_Estudiante = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), nullable=False)
    ArchivoURL = Column(String(255), nullable=False)
    FechaHoraEntrega = Column(DateTime, default=datetime.datetime.utcnow)
    Estado = Column(Boolean, default=True)

    # Relaciones
    tarea = relationship("Tarea", backref="entregas_recibidas")
    estudiante = relationship("Usuario", foreign_keys=[ID_Estudiante])