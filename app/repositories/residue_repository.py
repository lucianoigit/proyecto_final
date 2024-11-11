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
    
    def save_all(self, objetos):
        """
        Guarda una lista de objetos en la base de datos dentro de una transacción.
        Si ocurre un error, se realiza rollback y se aborta el proceso.
        """
        try:
            for objeto in objetos:
                self.session.add(objeto)
            self.session.commit()
            print("Todos los objetos guardados correctamente.")
        except Exception as e:
            self.session.rollback()
            print(f"Error durante el guardado: {e}")
            print("Proceso abortado, no se guardaron los cambios.")
            return False
        finally:
            self.session.close()
        return True

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
