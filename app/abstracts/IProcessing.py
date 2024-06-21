from abc import ABC, abstractmethod

class ProcessingInterface(ABC):
    @abstractmethod
    def calibrate(self, dirpath, prefix, image_format, square_size, width, height):
        pass

    @abstractmethod
    def undistorted_image(self, img):
        pass

    @abstractmethod
    def detected_objects(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        pass

    @abstractmethod
    def capture_image(self):
        pass
