from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Mensaje(Base):
    __tablename__ = 'Mensajes'

    ID_Mensaje = Column(Integer, primary_key=True, autoincrement=True)
    ID_Remitente = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), nullable=False)
    ID_Destinatario = Column(Integer, ForeignKey('Usuarios.ID_Usuario'), nullable=False)
    Contenido = Column(String(500), nullable=False)
    FechaEnvio = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones para saber quién es quién
    remitente = relationship("Usuario", foreign_keys=[ID_Remitente])
    destinatario = relationship("Usuario", foreign_keys=[ID_Destinatario])