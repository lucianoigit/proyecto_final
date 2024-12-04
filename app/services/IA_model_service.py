import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from app.abstracts.IMLModel import MLModelInterface

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

    def is_point_inside_workspace(self, x, y, area_de_trabajo):
        """
        Verifica si un punto (x, y) está dentro del área de trabajo definida por un polígono.
        `area_de_trabajo` es una lista de tuplas con las coordenadas de los vértices del polígono.
        """
        if len(area_de_trabajo) == 4:  # Asegurarse de que el área de trabajo tenga 4 vértices
            # Crear un polígono a partir de los vértices del área de trabajo (formato [(x1, y1), (x2, y2), ...])
            polygon = np.array(area_de_trabajo, np.int32)
            polygon = polygon.reshape((-1, 1, 2))  # Reshape necesario para cv2.pointPolygonTest

            # Usamos cv2.pointPolygonTest para comprobar si el punto está dentro del polígono
            return cv2.pointPolygonTest(polygon, (x, y), False) >= 0
        
        return False

    def run_model(self, img_path_or_img, confianza_minima=0.8, x_centroide=None, y_centroide=None, area_de_trabajo=None):
        """
        Ejecuta el modelo, calcula los centros de los objetos detectados, y filtra por clases y confianza.
        Además, dibuja el centroide general y los centros de las detecciones de los objetos.
        """
        try:
            # Cargar la imagen
            if isinstance(img_path_or_img, str):
                img = cv2.imread(img_path_or_img)
                if img is None:
                    print("Error: No se pudo leer la imagen desde la ruta proporcionada.")
                    return None, None
            else:
                img = img_path_or_img
            
            # Validar imagen
            if img is None or img.size == 0:
                print("Error: La imagen proporcionada es 'None' o está vacía.")
                return None, None

            # Ejecutar modelo
            results = self.model(img)
            if not results:
                print("No se detectaron objetos.")
                return None, None

            detections = results[0].boxes.data.cpu().numpy()
            names = self.model.names
            df = pd.DataFrame(detections, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class'])
            
            # Calcular el centro de cada detección
            df['center_x'] = (df['xmin'] + df['xmax']) / 2
            df['center_y'] = (df['ymin'] + df['ymax']) / 2

            # Convertir índices de clase a nombres
            df['class_name'] = df['class'].apply(lambda x: names[int(x)])

            # Filtrar por confianza mínima
            df_filtrado = df[df['confidence'] >= confianza_minima]

            # Dibujar las detecciones en la imagen
            for _, row in df_filtrado.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = row['class_name']
                confidence = row['confidence']
                center_x, center_y = row['center_x'], row['center_y']

                # Verificar si el centro de la detección está dentro del área de trabajo
                if area_de_trabajo and self.is_point_inside_workspace(center_x, center_y, area_de_trabajo):
                    # Si el centro está dentro del área de trabajo, lo dibujamos en verde
                    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Verde para detecciones dentro
                    cv2.circle(img, (int(center_x), int(center_y)), 5, (0, 255, 0), -1)  # Centro de la detección
                    cv2.putText(img, f"{class_name} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                else:
                    # Si el centro no está dentro, lo dibujamos en rojo
                    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)  # Rojo para detecciones fuera
                    cv2.circle(img, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)  # Centro de la detección en rojo
                    cv2.putText(img, f"{class_name} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Graficar el centroide general (x_centroide, y_centroide) si están definidos
            if x_centroide is not None and y_centroide is not None:
                cv2.circle(img, (int(x_centroide), int(y_centroide)), 5, (255, 0, 0), -1)  # Centroide general (azul)
                cv2.putText(img, "Centroide", (int(x_centroide), int(y_centroide) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            return df_filtrado, img
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None
