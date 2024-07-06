from datetime import datetime

class ResidueDTO:
    def __init__(self, nombre, categoria, confianza, x_min, x_max,y_min,y_max,fecha_deteccion, imagen_referencia):
        
        self.nombre = nombre
        self.categoria = categoria
        self.confianza = confianza
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.fecha_deteccion = fecha_deteccion
        self.imagen_referencia = imagen_referencia
