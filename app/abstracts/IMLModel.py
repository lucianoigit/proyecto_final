from abc import ABC, abstractmethod


class MLModelInterface(ABC):
    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def run_model(self, message):
        pass

    @abstractmethod
    def show_result(self):
        pass
