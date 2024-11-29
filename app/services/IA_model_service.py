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
            """             model = YOLO(self.model_path)
            model.export(format="ncnn") """
            # creates 'yolo11n_ncnn_model'
            # Load the exported NCNN model
            ncnn_model = YOLO("best_ncnn_model")
            return ncnn_model
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            return None
    def run_model(self, img_path_or_img, confianza_minima=0.6, roi=None):
        """
        Ejecuta el modelo, muestra detecciones antes del filtro, y procesa la imagen con las detecciones marcadas.
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

            # Dimensiones originales
            img_height, img_width = 480, 640  # Imagen es 640x480

            # Ejecutar modelo
            results = self.model(img)
            if not results:
                print("No se detectaron objetos.")
                return None, None

            detections = results[0].boxes.data.cpu().numpy()
            names = self.model.names
            df = pd.DataFrame(detections, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class'])

            # Escalar coordenadas al tamaño original
            scale_x, scale_y = img_width / 640, img_height / 640
            df['xmin'] *= scale_x
            df['xmax'] *= scale_x
            df['ymin'] *= scale_y
            df['ymax'] *= scale_y

            # Dibujar todas las detecciones (antes del filtro)
            for _, row in df.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = names[int(row['class'])]
                confidence = row['confidence']

                # Dibujar detección en la imagen
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)  # Azul para detecciones sin filtrar
                cv2.putText(img, f"{class_name} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Log: Detecciones antes del filtro
            print("\nDetecciones originales (antes del filtro):")
            for _, row in df.iterrows():
                print(f"Clase: {names[int(row['class'])]}, Confianza: {row['confidence']:.2f}, "
                    f"Coordenadas: ({row['xmin']:.2f}, {row['ymin']:.2f}) -> ({row['xmax']:.2f}, {row['ymax']:.2f})")

            # Filtrar por confianza mínima
            df_filtrado = df[df['confidence'] >= confianza_minima]

            # Filtrar por ROI si está definido
            if roi:
                x_min, y_min, x_max, y_max = roi
                df_filtrado = df_filtrado[
                    (df_filtrado['xmin'] >= x_min) & (df_filtrado['xmax'] <= x_max) &
                    (df_filtrado['ymin'] >= y_min) & (df_filtrado['ymax'] <= y_max)
                ]

            # Dibujar detecciones filtradas
            for _, row in df_filtrado.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = names[int(row['class'])]
                confidence = row['confidence']

                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Verde para detecciones filtradas
                cv2.putText(img, f"{class_name} {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Convertir índices de clase a nombres
            df_filtrado['class_name'] = df_filtrado['class'].apply(lambda x: names[int(x)])

            return df_filtrado, img
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None
