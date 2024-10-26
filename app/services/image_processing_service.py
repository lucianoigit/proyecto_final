from datetime import datetime
import threading
import time
from app.dbModels.ResidueDto import ResidueDTO
from app.repositories.residue_repository import ResidueRepository
import cv2
import numpy as np
import glob
from app.abstracts.IProcessing import ProcessingInterface
from app.services.IA_model_service import MLModelService
from app.abstracts.ITransport import TransportInterface  # Importación del servicio de transporte
from picamera2 import Picamera2

class ImageProcessingService(ProcessingInterface):

    def __init__(self, residue_repository: ResidueRepository, use_model: MLModelService, transport_service: TransportInterface):
        self.mtx = None
        self.dist = None
        self.residue_repository = residue_repository
        self.use_model = use_model
        self.transport_service = transport_service  # Servicio de transporte para conversiones
        self.detection_thread = None  # Variable para el hilo de detección
        self.picam2 = None  # Inicialización de la cámara

    def start_camera(self):
        """Inicializa y arranca la cámara."""
        if self.picam2 is None:
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_still_configuration())
            self.picam2.start()
            print("Cámara iniciada.")

    def stop_camera(self):
        """Detiene y libera la cámara."""
        if self.picam2 is not None:
            self.picam2.stop()
            self.picam2 = None
            print("Cámara detenida.")

    def capture_image(self):
        """Captura una imagen usando la cámara inicializada."""
        if self.picam2 is None:
            print("Error: La cámara no está inicializada.")
            return None
        try:
            time.sleep(2)  # Esperar un poco para que la cámara ajuste el enfoque y la exposición
            foto = self.picam2.capture_array()
            return foto
        except Exception as e:
            print(f"Error al capturar la imagen: {e}")
            return None
        
    def detected_objects(self, img_undistorted, confianza_minima=0.2, relation_x=0, relation_y=0, roi=None):
        try:
            print("Procesando imagen...")
            df_filtrado, img_resultado = self.use_model.run_model(img_undistorted, confianza_minima,roi)
            print("Imagen procesada.", df_filtrado)

            if df_filtrado is not None:
                residue_list = []
                for _, row in df_filtrado.iterrows():
                    print(f"Procesando fila: {row}")

                    # Convertir las coordenadas de píxeles a milímetros usando relaciones definidas
                    x_min_mm = row['xmin'] * relation_x
                    y_min_mm = row['ymin'] * relation_y
                    x_max_mm = row['xmax'] * relation_x
                    y_max_mm = row['ymax'] * relation_y

                    # Crear el ResidueDTO con coordenadas convertidas
                    residue_dto = ResidueDTO(
                        nombre=row['class_name'],
                        categoria=row['class'],
                        confianza=row['confidence'],
                        x_min=x_min_mm,
                        y_min=y_min_mm,
                        x_max=x_max_mm,
                        y_max=y_max_mm,
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

    def detected_objects_in_background(self, img_undistorted, confianza_minima=0.2, callback=None, relation_x=0,relation_y=0,roi=None):
        """
        Ejecuta detected_objects en un hilo separado para no bloquear la interfaz.
        El `callback` se llamará con los resultados cuando la detección termine.
        """

        def run_detection():
            df_filtrado, img_resultado, residue_list = self.detected_objects(img_undistorted, confianza_minima,roi)

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
        
    def save_residue_list(self, residue_list):
        print(f"Residuos recolectados en BDD:", residue_list)
        # Implementar la lógica de guardado en la base de datos si es necesario

