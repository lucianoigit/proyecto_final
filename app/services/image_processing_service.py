from datetime import datetime
import threading
from app.dbModels.ResidueDto import ResidueDTO
from app.repositories.residue_repository import ResidueRepository
import cv2
import numpy as np
import glob
from app.abstracts.IProcessing import ProcessingInterface
from app.services.IA_model_service import MLModelService
from picamera2 import Picamera2

class ImageProcessingService(ProcessingInterface):

    def __init__(self, residue_repository: ResidueRepository, use_model: MLModelService):
        self.mtx = None
        self.dist = None
        self.residue_repository = residue_repository
        self.use_model = use_model
        
        self.detection_thread = None  # Variable para el hilo de detección

    def detected_objects(self, img_undistorted, confianza_minima=0.2):
        try:
            print("Procesando imagen...")
            df_filtrado, img_resultado = self.use_model.run_model(img_undistorted, confianza_minima)
            print("Imagen procesada.", df_filtrado)

            if df_filtrado is not None:
                residue_list = []
                for _, row in df_filtrado.iterrows():
                    print(f"Procesando fila: {row}")
                    residue_dto = ResidueDTO(
                        nombre=row['class_name'],
                        categoria=row['class'],
                        confianza=row['confidence'],
                        x_min=row['xmin'],
                        y_min=row['ymin'],
                        x_max=row['xmax'],
                        y_max=row['ymax'],
                        fecha_deteccion=datetime.now(),
                        imagen_referencia="default_image"
                    )
                    print("ResidueDTO", residue_dto)
                    residue_list.append(residue_dto)
                print("ResidueList", residue_list)
                return df_filtrado, img_resultado, residue_list
            else:
                print("No hay detecciones.")
                return None, None, []

        except Exception as e:
            print(f"Error durante la detección: {e}")
            return None, None, []

    def detected_objects_in_background(self, img_undistorted, confianza_minima=0.2, callback=None):
        """
        Ejecuta detected_objects en un hilo separado para no bloquear la interfaz.
        El `callback` se llamará con los resultados cuando la detección termine.
        """

        def run_detection():
            df_filtrado, img_resultado, residue_list = self.detected_objects(img_undistorted, confianza_minima)

            # Aquí usamos el método after para actualizar la UI en el hilo principal
            if callback:
                # Si necesitas pasar los datos de vuelta al hilo principal para actualizar la interfaz
                self.root.after(0, lambda: callback(df_filtrado, img_resultado, residue_list))

        # Crear y arrancar el hilo
        self.detection_thread = threading.Thread(target=run_detection)
        self.detection_thread.start()


    def wait_for_detection(self):
        """ Espera a que el hilo de detección termine, si existe. """
        if self.detection_thread:
            self.detection_thread.join()

    def calibrate(self, dirpath, prefix, image_format, square_size, width, height):
        images = glob.glob(f"{dirpath}/{prefix}*.{image_format}")
        objp = np.zeros((width * height, 3), np.float32)
        objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2) * square_size
        objpoints = []
        imgpoints = []

        for fname in images:
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, (width, height), None)
            if ret:
                objpoints.append(objp)
                imgpoints.append(corners)

        if not objpoints or not imgpoints:
            print("No se encontraron imágenes válidas para la calibración.")
            return None, None

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        self.mtx, self.dist = mtx, dist
        return mtx, dist

    def undistorted_image(self, img):
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        img_undistorted = cv2.undistort(img, self.mtx, self.dist, None, newcameramtx)
        return img_undistorted
    """ 
    def detected_objects(self, img_undistorted, confianza_minima=0.2):
        try:
            print("Procesando imagen...")
            df_filtrado, img_resultado = self.use_model.run_model(img_undistorted, confianza_minima)
            print("Imagen procesada.", df_filtrado)

            if df_filtrado is not None:
     
                print(df_filtrado)

                residue_list = []
                for _, row in df_filtrado.iterrows():
                    print(f"Procesando fila: {row}")
                    residue_dto = ResidueDTO(
                        nombre=row['class_name'],  
                        categoria=row['class'],  
                        confianza=row['confidence'],
                        x_min=row['xmin'],
                        y_min=row['ymin'],
                        x_max=row['xmax'],
                        y_max=row['ymax'],
                        fecha_deteccion=datetime.now(),
                        imagen_referencia="default_image"
                    )
                    print("ResidueDTO",residue_dto)
                    residue_list.append(residue_dto)
                print("ResidueList",residue_list)
                return df_filtrado, img_resultado, residue_list
            else:
                print("No hay detecciones.")
                return None, None, []

        except Exception as e:
            print(f"Error durante la detección: {e}")
            return None, None, [] """
        
    def save_residue_list(self, residue_list):
        print(f"residuos recolectados en bdd", residue_list)
        """   for residue_dto in residue_list:
            print(f"residuo particular en bdd ", residue_dto)
            self.residue_repository.add_residue(
                nombre=residue_dto.nombre,
                categoria=residue_dto.categoria,
                confianza=residue_dto.confianza,
                x_min=residue_dto.x_min,
                y_min=residue_dto.y_min,
                x_max=residue_dto.x_max,
                y_max=residue_dto.y_max,
                fecha_deteccion=residue_dto.fecha_deteccion,
                imagen_referencia=residue_dto.imagen_referencia
            ) """

    def capture_image(self):
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration())
        picam2.start()
        time.sleep(2)  # Esperar un poco para que la cámara ajuste el enfoque y la exposición
        foto = picam2.capture_array()
        picam2.stop()
        return foto
