from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.dialects.mssql import DATETIME  # <-- IMPORTANTE: Importamos el DATETIME clásico de SQL Server
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Tarea(Base):
    __tablename__ = 'Tareas'

    ID_Tarea = Column(Integer, primary_key=True, autoincrement=True)
    ID_Grupo = Column(Integer, ForeignKey('Grupos.ID_Grupo'), nullable=False)
    Titulo = Column(String(150), nullable=False)
    Descripcion = Column(Text, nullable=True) # Regresamos a Text como en tu BD
    ArchivosAdicionales = Column(String(255), nullable=True)
    
    # Usamos el DATETIME en mayúsculas importado de mssql
    FechaAsignacion = Column(DATETIME, default=datetime.datetime.utcnow)
    FechaLimite = Column(DATETIME, nullable=False)
    
    Estado = Column(Boolean, default=True)

    # Relación bidireccional con el grupo
    grupo = relationship("Grupo", backref="tareas_asignadas")