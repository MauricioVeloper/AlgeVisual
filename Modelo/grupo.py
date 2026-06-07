from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Grupo(Base):
    __tablename__ = 'Grupos'

    ID_Grupo = Column(Integer, primary_key=True, autoincrement=True)
    CodigoInvitacion = Column(String(20), unique=True, nullable=False)
    Nombre = Column(String(100), nullable=False)
    Ciclo = Column(String(50))
    Horario = Column(String(100))
    EspacioFisico = Column(String(100))
    # Llave foránea que apunta al ID del Docente
    ID_Docente = Column(Integer, ForeignKey('Docentes.ID_Docente'), nullable=False)
    Estado = Column(Boolean, default=True)

    # Relación bidireccional para poder sacar el nombre del maestro fácilmente en el HTML
    docente = relationship("Docente", backref="grupos_asignados", lazy="joined")

    def __repr__(self):
        return f"<Grupo {self.Nombre} - {self.CodigoInvitacion}>"