import cv2
import numpy as np
from app.abstracts.ITransport import TransportInterface

class TransportService(TransportInterface):
    def __init__(self):
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.pixels_per_mm_x = None
        self.pixels_per_mm_y = None
        self.is_scrolling = False

    def generate_square(self, x1: int, y1: int, x2: int, y2: int):
        """
        Genera un cuadrado con coordenadas dadas y lo almacena en la clase.
        """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        top_left = (self.x1, self.y1)
        bottom_right = (self.x2, self.y2)
        return self.x1,self.x2,self.y1,self.y2

    def calculate_center(self,x1,x2,y1,y2):
        """
        Calcula y devuelve las coordenadas del centro del cuadrado.
        """
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return (center_x, center_y)

    def calibrate_to_physical_space(self, physical_width_mm: float, physical_height_mm: float):
        """
        Calibra el cuadrado a unidades físicas.
        Calcula cuántos píxeles corresponden a cada milímetro en x e y.
        """
        print("inicia calibracion")
        pixel_width = abs(self.x2 - self.x1)
        pixel_height = abs(self.y2 - self.y1)
        self.pixels_per_mm_x = pixel_width / physical_width_mm
        self.pixels_per_mm_y = pixel_height / physical_height_mm
        
        print (" se termino la calibracion", "x  en mm", self.pixels_per_mm_x)
        print (" se termino la calibracion", "y  en mm", self.pixels_per_mm_y)
        
        return  self.pixels_per_mm_x,self.pixels_per_mm_y

    def convert_pixels_to_mm(self, x_pixels, y_pixels,pixels_per_mm_x,pixels_per_mm_y):
        """
        Convierte coordenadas en píxeles a milímetros usando la calibración.
        """
        if pixels_per_mm_x is None or pixels_per_mm_y is None:
            raise ValueError("Debes calibrar antes de convertir.")
        x_mm = x_pixels / pixels_per_mm_x
        y_mm = y_pixels / pixels_per_mm_y
        return x_mm, y_mm

    def get_offset(self,x1,x2,pixels_per_mm_x):
        """
        Calcula el desplazamiento (offset) en milímetros basado en las coordenadas.
        """
        if pixels_per_mm_x is None:
            raise ValueError("Debes calibrar antes de calcular el offset.")
        
        # Cálculo del offset en píxeles y luego conversión a milímetros
        offset_pixels = x1 - x2
        offset_mm = offset_pixels / pixels_per_mm_x
        return offset_mm

    def scroll(self, command: str):
        """
        Activa o desactiva el desplazamiento según el comando recibido.
        """
        if command == "OK":
            self.is_scrolling = True
            status = "activado"
        elif command == "NO":
            self.is_scrolling = False
            status = "desactivado"
        else:
            status = "comando no reconocido"
        
        print(f"Desplazamiento {status}")
        return self.is_scrolling
