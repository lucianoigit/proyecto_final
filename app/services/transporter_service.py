import cv2
import numpy as np
from app.abstracts.ITransport import TransportInterface

class TransportService(TransportInterface):
    
    def __init__(self):
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.is_scrolling = False  # Estado de desplazamiento (activado/desactivado)
    
    def generate_square(self, x1: int, y1: int, x2: int, y2: int):
        """
        Genera un cuadrado con coordenadas dadas y lo almacena en la clase.
        Luego lo dibuja en una imagen con OpenCV.
        """
        # Guardar las coordenadas del cuadrado
        self.x1 = x1
        self.y1 = y1 
        self.x2 = x2
        self.y2 = y2
        
        # Crear una imagen en blanco de 500x500 píxeles
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        
        # Dibujar el cuadrado en la imagen (usando las coordenadas dadas)
        color = (255, 255, 255)  # Color blanco para el cuadrado
        thickness = 2  # Grosor del borde
        top_left = (self.x1, self.y1)
        bottom_right = (self.x2, self.y2)
        
        cv2.rectangle(img, top_left, bottom_right, color, thickness)
        
        # Mostrar la imagen con el cuadrado generado
        cv2.imshow('Cuadrado generado', img)
        cv2.waitKey(0)  
        cv2.destroyAllWindows()

        return {"top_left": top_left, "bottom_right": bottom_right}  # Devuelve las coordenadas del cuadrado

    def calculate_center(self):
        """
        Calcula y devuelve las coordenadas del centro del cuadrado.
        """
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def scroll(self, command: str):
        """
        Activa o desactiva el desplazamiento según el comando recibido.
        Si el comando es "OK", activa el desplazamiento.
        Si el comando es "NO", desactiva el desplazamiento.
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

    def get_offset(self):
        """
        Calcula el desplazamiento basado en las coordenadas.
        """
        return self.x1 - self.x2
