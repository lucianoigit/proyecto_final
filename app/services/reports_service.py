from app.repositories.residue_repository import ResidueRepository

class ReportsService():
    def __init__(self, residue_repository: ResidueRepository):
        self.residue_repository = residue_repository

    def get_all_rankings(self):
        return self.residue_repository.get_all_residues()

    def get_ranking_by_id(self, id: int):
        return self.residue_repository.find_by_id(id)

    def delete_ranking(self, id: int):
        return self.residue_repository.delete_residue(id)

    def count_ranking_by_category(self):
        return self.residue_repository.count_by_category()

    def filter_by_category(self, category: str):
        return self.residue_repository.find_by_category(category)

    def filter_by_confidence(self, min_confidence: float):
        return self.residue_repository.find_by_confidence(min_confidence)
