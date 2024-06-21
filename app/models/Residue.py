""" from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Residue(Base):
    __tablename__ = 'objetos'

    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    categoria = Column(String)
    confianza = Column(Float)
    x_min = Column(Integer)
    y_min = Column(Integer)
    x_max = Column(Integer)
    y_max = Column(Integer)
    fecha_deteccion = Column(DateTime)
    ubicacion = Column(String)
    imagen_referencia = Column(String)
 """