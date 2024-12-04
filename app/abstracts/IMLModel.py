from abc import ABC, abstractmethod


class MLModelInterface(ABC):
    @abstractmethod
    def load_model(self,model_path):
        pass

    @abstractmethod
    def run_model(self,img_path_or_img, confianza_minima=0.8,x_centroide=None, y_centroide=None, area_de_trabajo=None):
        pass

    @abstractmethod
    def is_point_inside_workspace(self, x, y, area_de_trabajo):
        pass
    
    @abstractmethod  
    def inicialiced_model(self,img):
        pass