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
    def __init__(self, residue_repository: ResidueRepository, use_model: MLModelService, transport_service: TransportInterface, picamera: Picamera2):
        self.mtx = None
        self.dist = None
        self.residue_repository = residue_repository
        self.use_model = use_model
        self.transport_service = transport_service
        self.picam2 = picamera  # Inyección de la cámara

    def capture_image(self):
        # Detener la cámara en caso de que esté activa

        try:
            img_rgb = self.picam2.capture_array()
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            return img_bgr
        except Exception as e:
            print(f"Error capturando la imagen: {e}")
            return None

    def close_camera(self):
        if self.picam2.is_streaming:
            self.picam2.stop()
            print("Cámara detenida.")

    def undistorted_image(self, img):
        """Aplica la corrección de distorsión en la imagen y verifica el formato."""
        try:
            h, w = img.shape[:2]
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
            img_undistorted = cv2.undistort(img, self.mtx, self.dist, None, newcameramtx)

            print(f"Imagen corregida sin distorsión: {img_undistorted.shape}, dtype: {img_undistorted.dtype}")
            return img_undistorted
        except Exception as e:
            print(f"Error en undistorted_image: {e}")
            return None

    def detected_objects(self, img_undistorted, confianza_minima=0.2,tamano_entrada=(416, 416), relation_x=0.00000, relation_y=0.00000, roi=None):
        try:
            print("Procesando imagen...")
            print("Tipo de relation_x:", type(relation_x), "| Valor de relation_x:", relation_x)
            print("Tipo de relation_y:", type(relation_y), "| Valor de relation_y:", relation_y)
            print("Confianza mínima:", confianza_minima)
            print("ROI:", roi)

            df_filtrado, img_resultado = self.use_model.run_model(img_undistorted, confianza_minima, roi)
           
           
           
            print("Imagen procesada. DataFrame resultante:", df_filtrado)

            if df_filtrado is not None:
                residue_list = []
                for _, row in df_filtrado.iterrows():
                    print(f"Procesando fila: {row}")
                    
                    # Convertir las coordenadas de píxeles a milímetros usando relaciones definidas
                    x_min_mm = row['xmin'] * relation_x
                    y_min_mm = row['ymin'] * relation_y
                    x_max_mm = row['xmax'] * relation_x
                    y_max_mm = row['ymax'] * relation_y
                    print(f"x_min_mm: {x_min_mm}, y_min_mm: {y_min_mm}, x_max_mm: {x_max_mm}, y_max_mm: {y_max_mm}")

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
                    print("ResidueDTO creado:", residue_dto)
                    residue_list.append(residue_dto)
                
                print("Lista de residuos detectados:", residue_list)
                return df_filtrado, img_resultado, residue_list
            else:
                print("No hay detecciones.")
                return None, None, []

        except Exception as e:
            print(f"Error durante la detección: {e}")
            return None, None, []

    def detected_objects_in_background(self, img_undistorted, confianza_minima=0.2, callback=None, relation_x=0.00000,relation_y=0.0000,roi=None):
        """
        Ejecuta detected_objects en un hilo separado para no bloquear la interfaz.
        El `callback` se llamará con los resultados cuando la detección termine.
        """

        def run_detection():
            df_filtrado, img_resultado, residue_list = self.detected_objects(img_undistorted, confianza_minima,None,relation_x,relation_y,roi)

            # Aquí usamos el método after para actualizar la UI en el hilo principal
            if callback:
                # Si necesitas pasar los datos de vuelta al hilo principal para actualizar la interfaz
                
                callback(df_filtrado, img_resultado, residue_list)

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


    def save_residue_list(self, residue_list):
        print(f"Residuos recolectados en BDD:", residue_list)
        # Implementar la lógica de guardado en la base de datos si es necesario
    
    def show_result(self, df_filtrado, img):
        if df_filtrado is not None and not df_filtrado.empty and img is not None:
            for index, row in df_filtrado.iterrows():
                # Definir coordenadas del rectángulo
                x_min, y_min, x_max, y_max = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                
                # Dibujar el rectángulo de detección
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                
                # Calcular y dibujar el centroide
                centro_x = (x_min + x_max) // 2
                centro_y = (y_min + y_max) // 2
                cv2.circle(img, (centro_x, centro_y), 5, (255, 0, 0), -1)  # Dibuja el centro en azul
                
                # Agregar texto con nombre de la clase y nivel de confianza
                class_name = row['class_name']
                confidence = row['confidence']
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(img, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                print(f"Objeto detectado: {class_name} con confianza {confidence:.2f} en ({centro_x}, {centro_y})")

            return img
        else:
            if img is not None:
                print("No hay resultados para mostrar.")
                return img
                
