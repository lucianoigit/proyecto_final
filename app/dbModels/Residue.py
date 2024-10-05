import uuid
from database.db import Base
from sqlalchemy import Column, Integer, String, Float, DateTime




class Residue(Base):
    __tablename__ = 'objetos'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # Usar UUID como id
    nombre = Column(String)
    categoria = Column(String)
    confianza = Column(Float)
    x_min = Column(Integer)
    y_min = Column(Integer)
    x_max = Column(Integer)
    y_max = Column(Integer)
    fecha_deteccion = Column(DateTime)
    imagen_referencia = Column(String)


    def __repr__(self):
        return f"Residue(id={self.id}, nombre={self.nombre}, categoria={self.categoria}, confianza={self.confianza}, x_min={self.x_min}, y_min={self.y_min}, x_max={self.x_max}, y_max={self.y_max}, fecha_deteccion={self.fecha_deteccion}, imagen_referencia={self.imagen_referencia})"

    def __str__(self):
        return f"ID: {self.id}, Nombre: {self.nombre}, Categoría: {self.categoria}, Confianza: {self.confianza}, Fecha: {self.fecha_deteccion}"
