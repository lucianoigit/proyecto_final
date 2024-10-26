from abc import ABC, abstractmethod

class ProcessingInterface(ABC):
    @abstractmethod
    def calibrate(self, dirpath, prefix, image_format, square_size, width, height):
        pass
    @abstractmethod
    def start_camera(self):
        pass
    @abstractmethod
    def undistorted_image(self, img):
        pass
    @abstractmethod
    def stop_camera(self):
        pass
    @abstractmethod
    def detected_objects_in_background(self, img_undistorted, confianza_minima=0.2, callback=None,relation_x=0,relation_y=0):
        pass
    @abstractmethod
    def detected_objects(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416),relation_x=0,relation_y=0):
        pass

    @abstractmethod
    def capture_image(self):
        pass
    
    @abstractmethod
    def save_residue_list(self):
        pass
