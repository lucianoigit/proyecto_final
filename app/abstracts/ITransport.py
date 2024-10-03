from abc import ABC, abstractmethod

class TransportInterface(ABC):
    @abstractmethod
    def generate_square(self, x1,y1,x2,y2):
        pass

    @abstractmethod
    def scroll(self, command):
        pass

    @abstractmethod
    def get_offset(self):
        pass
    
    @abstractmethod
    def calculate_center(self):
        pass
    