import cv2
import numpy as np
import glob
import torch
from app.abstracts.IProcessing import ProcessingInterface

class ImageProcessingService(ProcessingInterface):
    def __init__(self):
        self.mtx = None
        self.dist = None

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

    def detected_objects(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        try:
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
            resultados = model(img_undistorted)
            imagenresutado = resultados.show()
            df = resultados.pandas().xyxy[0]
            df_filtrado = df[df['confidence'] >= confianza_minima]
            df_filtrado['x_center'] = (df_filtrado['xmin'] + df_filtrado['xmax']) / 2
            df_filtrado['y_center'] = (df_filtrado['ymin'] + df_filtrado['ymax']) / 2
            return df_filtrado, imagenresutado
        except Exception as e:
            print(f"Error al detectar objetos: {e}")
            return [], None

    def capture_image(self):
        cam = cv2.VideoCapture(0)
        ret, foto = cam.read()
        cam.release()
        return foto
