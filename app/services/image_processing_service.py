from datetime import datetime
from app.dbModels.ResidueDto import ResidueDTO
from app.repositories.residue_repository import ResidueRepository
import cv2
import numpy as np
import glob
from app.abstracts.IProcessing import ProcessingInterface
from app.services.IA_model_service import MLModelService

class ImageProcessingService(ProcessingInterface):

    def __init__(self, residue_repository: ResidueRepository, use_model: MLModelService):
        self.mtx = None
        self.dist = None
        self.residue_repository = residue_repository
        self.use_model = use_model

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

    def detected_objects(self, img_undistorted, confianza_minima=0.2):
        try:
            print("Procesando imagen...")
            df_filtrado, img_resultado = self.use_model.run_model(img_undistorted, confianza_minima)
            print("Imagen procesada.", df_filtrado)

            if df_filtrado is not None:
                self.use_model.show_result(df_filtrado, img_resultado)
                print(df_filtrado)

                residue_list = []
                for _, row in df_filtrado.iterrows():
                    residue_dto = ResidueDTO(
                        nombre=row['class_name'],  # Usar el nombre de la clase
                        categoria=row['class'],  # Usar el nombre de la clase
                        confianza=row['confidence'],
                        x_min=row['xmin'],
                        y_min=row['ymin'],
                        x_max=row['xmax'],
                        y_max=row['ymax'],
                        fecha_deteccion=datetime.now(),
                        imagen_referencia="default_image"
                    )
                    residue_list.append(residue_dto)
                
                return df_filtrado, img_resultado, residue_list
            else:
                print("No hay detecciones.")
                return None, None, []

        except Exception as e:
            print(f"Error durante la detección: {e}")
            return None, None, []
        
    def save_residue_list(self, residue_list):
        print(f"residuos recolectados en bdd", residue_list)
        for residue_dto in residue_list:
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
            )

    def capture_image(self):
        cam = cv2.VideoCapture(0)
        ret, foto = cam.read()
        cam.release()
        return foto
