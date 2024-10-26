from abc import ABC, abstractmethod

class TransportInterface(ABC):
    @abstractmethod
    def generate_square(self, x1,y1,x2,y2):
        pass
    @abstractmethod
    def calibrate_to_physical_space(physical_width_mm, physical_height_mm):
        pass

    @abstractmethod
    def scroll(self, command):
        pass

    @abstractmethod
    def get_offset(self,x1,x2,pixels_per_mm_x):
        pass
    
    @abstractmethod
    def calculate_center(self,x,y):
        pass
    
    @abstractmethod
    def convert_pixels_to_mm(self, x_pixels, y_pixels,pixels_per_mm_x,pixels_per_mm_y):
        pass
    