from sqlalchemy import Column, Integer, String

from database.base import Base


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    email = Column(String, unique=True)
