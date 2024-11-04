import cv2
import numpy as np
from app.abstracts.ITransport import TransportInterface

class TransportService(TransportInterface):
    def __init__(self):
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.x3 = 0
        self.y3 = 0
        self.x4 = 0
        self.y4 = 0
        self.pixels_per_mm_x = None
        self.pixels_per_mm_y = None
        self.is_scrolling = False

    def generate_square(self, x1, y1, x2, y2, x3, y3, x4, y4):
        self.x1, self.y1, self.x2, self.y2, self.x3, self.y3, self.x4, self.y4 = x1, y1, x2, y2, x3, y3, x4, y4
        return self.x1, self.y1, self.x2, self.y2, self.x3, self.y3, self.x4, self.y4

    def calculate_center(self, x1, x3, y1, y3):
        center_x = (x1 + x3) // 2
        center_y = (y1 + y3) // 2
        return (center_x, center_y)

    def calibrate_to_physical_space(self, physical_width_mm, physical_height_mm,x2,x1,y4,y1):
        pixel_width = abs(x2 - x1)
        pixel_height = abs(y4 - y1)
        self.pixels_per_mm_x = pixel_width / physical_width_mm
        self.pixels_per_mm_y = pixel_height / physical_height_mm

        print("Calibración completada: píxeles por mm en x:", self.pixels_per_mm_x, "y en y:", self.pixels_per_mm_y)
        return self.pixels_per_mm_x, self.pixels_per_mm_y

    def convert_pixels_to_mm(self, x_pixels, y_pixels, pixels_per_mm_x, pixels_per_mm_y):
        if pixels_per_mm_x is None or pixels_per_mm_y is None:
            raise ValueError("Debes calibrar antes de convertir.")
        x_mm = x_pixels / pixels_per_mm_x
        y_mm = y_pixels / pixels_per_mm_y
        return x_mm, y_mm

    def get_offset(self, x1, x2, pixels_per_mm_x):
        offset_pixels = x1 - x2
        offset_mm = offset_pixels / pixels_per_mm_x
        return offset_mm
