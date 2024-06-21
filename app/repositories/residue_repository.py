""" from sqlalchemy.orm import Session
from models import Residue

class ResiudeRepository:
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

    def find_by_category(self, categoria):
        return self.session.query(Residue).filter(Residue.categoria == categoria).all()
    
    def find_by_imageName(self, imageName):
        return self.session.query(Residue).filter(Residue.categoria == categoria).all()
 """