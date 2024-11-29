from abc import ABC, abstractmethod


class MLModelInterface(ABC):
    @abstractmethod
    def load_model(self,model_path):
        pass

    @abstractmethod
    def run_model(self, message,confianza,roi):
        pass


