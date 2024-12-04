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
    
    def run_model(self, img_path_or_img, confianza_minima=0.8, roi=None,x_centroide=None, y_centroide=None):
        """
        Ejecuta el modelo, calcula los centros de los objetos detectados, y filtra por clases, confianza y ROI.
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

            # Log: Detecciones originales (antes del filtro)
            print("\nDetecciones originales (antes del filtro):")
            for _, row in df.iterrows():
                print(f"Clase: {row['class_name']}, Confianza: {row['confidence']:.2f}, "
                    f"Centro: ({row['center_x']:.2f}, {row['center_y']:.2f})")

            # Filtrar por confianza mínima
            df_filtrado = df[df['confidence'] >= confianza_minima]



        # Dibujar el ROI en la imagen si está definido
            if roi:
                x_min, y_min, x_max, y_max = roi
                print(f"\nDibujando ROI: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 255), 2)  # Amarillo para el ROI

                # Filtrar detecciones cuyo centro esté dentro del ROI
                df_filtrado = df_filtrado[
                    (df_filtrado['center_x'] >= x_min) & (df_filtrado['center_x'] <= x_max) &
                    (df_filtrado['center_y'] >= y_min) & (df_filtrado['center_y'] <= y_max)
                ]

            # Dibujar detecciones filtradas
            for _, row in df_filtrado.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = row['class_name']
                confidence = row['confidence']
                center_x, center_y = row['center_x'], row['center_y']

                # Dibujar rectángulo y centro
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Verde para detecciones filtradas
                cv2.circle(img, (int(center_x), int(center_y)), 5, (0, 255, 0), -1)  # Centro del rectángulo
                cv2.putText(img, f"{class_name} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Si se proporcionan los parámetros `x_centroide` y `y_centroide`, dibujar ese punto
            if x_centroide is not None and y_centroide is not None:
                print(f"Marcando centroide en: ({x_centroide}, {y_centroide})")
                # Dibujar el centroide global
                cv2.circle(img, (int(x_centroide), int(y_centroide)), 10, (255, 0, 0), -1)  # Rojo para el centroide global
                cv2.putText(img, "Centroide Global", (int(x_centroide), int(y_centroide) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)


            return df_filtrado, img
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None
