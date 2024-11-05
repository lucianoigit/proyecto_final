import cv2
from ultralytics import YOLO
from app.abstracts.IMLModel import MLModelInterface
import pandas as pd


class MLModelService(MLModelInterface):
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = self.load_model()

    def load_model(self):
        try:
            # Cargar el modelo YOLOv5 personalizado
            model = YOLO(self.model_path)
            return model
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            return None

    def run_model(self, img_path_or_img, confianza_minima=0.2, roi=None):
        """
        Ejecuta el modelo de clasificación en una región específica de la imagen.
        
        :param img_path_or_img: Ruta de la imagen o imagen en formato numpy.
        :param confianza_minima: Nivel mínimo de confianza para considerar una detección.
        :param roi: Región de interés en formato (x_min, y_min, x_max, y_max). Si es None, se usará toda la imagen.
        :return: DataFrame con detecciones filtradas y la imagen procesada.
        """
        try:
            # Verificar si la entrada es una ruta de archivo o una imagen
            if isinstance(img_path_or_img, str):
                # Leer la imagen desde la ruta del archivo
                img = cv2.imread(img_path_or_img)
                if img is None:
                    print("Error al leer la imagen.")
                    return None, None
                img_path = img_path_or_img
            else:
                # Asumir que la entrada es una imagen en formato numpy
                img = img_path_or_img
                img_path = None

            if roi:
                x_min, y_min, x_max, y_max = roi
                print(f"ROI definido: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
                
                # Verificar que las coordenadas estén dentro de la imagen
                if x_min < 0 or y_min < 0 or x_max > img.shape[1] or y_max > img.shape[0]:
                    print("Error: Las coordenadas del ROI están fuera del rango de la imagen.")
                    return None, None 

            # Ejecutar el modelo en la imagen (o la región recortada)
            results = self.model(img)
            if not results:
                print("No se detectaron objetos.")
                return None, None

            # Obtener las detecciones
            detections = results[0].boxes.data.cpu().numpy()  # Obtener detecciones del primer resultado
            print ("detectados", detections)
            names = self.model.names  # Obtener los nombres de las clases desde el modelo
            df = pd.DataFrame(detections, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class'])

            # Filtrar por confianza mínima
            df_filtrado = df[df['confidence'] >= confianza_minima]

            # Ajustar las coordenadas de las detecciones si se recortó la imagen
            if roi:
                x_min, y_min, _, _ = roi
                df_filtrado[['xmin', 'xmax']] += x_min
                df_filtrado[['ymin', 'ymax']] += y_min

            # Convertir el índice de clase a nombre de clase
            df_filtrado['class_name'] = df_filtrado['class'].apply(lambda x: names[int(x)])
            return df_filtrado, img
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None



    
