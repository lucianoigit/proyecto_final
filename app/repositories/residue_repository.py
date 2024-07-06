from app.dbModels.Residue import Residue
from sqlalchemy.orm import Session
from sqlalchemy import func

class ResidueRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_residue(self, **kwargs):
        obj = Residue(**kwargs)
        self.session.add(obj)
        self.session.commit()
        return obj

    def update_residue(self, obj_id, **kwargs):
        obj = self.session.query(Residue).filter(Residue.id == obj_id).one()
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.session.commit()
        return obj

    def find_by_id(self, id: int):
        return self.session.query(Residue).filter(Residue.id == id).one_or_none()

    def get_all_residues(self):
        return self.session.query(Residue).all()

    def delete_residue(self, id: int):
        obj = self.session.query(Residue).filter(Residue.id == id).one()
        self.session.delete(obj)
        self.session.commit()
        return obj

    def find_by_category(self, category: str):
        return self.session.query(Residue).filter(Residue.categoria == category).all()

    def count_by_category(self):
        return self.session.query(Residue.categoria, func.count(Residue.categoria)).group_by(Residue.categoria).all()

    def find_by_confidence(self, min_confidence: float):
        return self.session.query(Residue).filter(Residue.confianza >= min_confidence).all()

    def find_by_image_name(self, name: str):
        return self.session.query(Residue).filter(Residue.imagen_referencia == imageName).all()
