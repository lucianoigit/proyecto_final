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
        Ejecuta el modelo de clasificación, ajusta coordenadas a las dimensiones originales (640x480),
        filtra por confianza y ROI, y dibuja rectángulos en la imagen.
        """
        try:
            # Verificar si la entrada es una ruta de archivo o una imagen
            if isinstance(img_path_or_img, str):
                img = cv2.imread(img_path_or_img)  # Leer la imagen desde la ruta del archivo
                if img is None:
                    print("Error: No se pudo leer la imagen desde la ruta proporcionada.")
                    return None, None
            else:
                img = img_path_or_img  # Asumir que la entrada es una imagen en formato numpy

            # Validación para retornar error si la imagen es None
            if img is None or img.size == 0:
                print("Error: La imagen proporcionada es 'None' o está vacía.")
                return None, None

            # Dimensiones originales de la imagen
            img_height, img_width = 480, 640  # Imagen es 640x480

            # Ejecutar el modelo en la imagen completa
            results = self.model(img)
            if not results:
                print("No se detectaron objetos.")
                return None, None

            # Obtener las detecciones
            detections = results[0].boxes.data.cpu().numpy()  # Obtener detecciones del primer resultado
            names = self.model.names  # Obtener los nombres de las clases desde el modelo
            df = pd.DataFrame(detections, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class'])

            # Escalar las coordenadas de las detecciones al tamaño de la imagen original
            scale_x, scale_y = img_width / 640, img_height / 640
            df['xmin'] *= scale_x
            df['xmax'] *= scale_x
            df['ymin'] *= scale_y
            df['ymax'] *= scale_y

            # Log: Detecciones originales después de escalar
            print("\nDetecciones originales (escaladas):")
            for _, row in df.iterrows():
                print(f"Clase: {names[int(row['class'])]}, Confianza: {row['confidence']:.2f}, "
                    f"Coordenadas: ({row['xmin']:.2f}, {row['ymin']:.2f}) -> ({row['xmax']:.2f}, {row['ymax']:.2f})")

            # Filtrar por confianza mínima
            df_filtrado = df[df['confidence'] >= confianza_minima]

            # Log: Detecciones después del filtrado por confianza
            print("\nDetecciones después del filtrado por confianza:")
            for _, row in df_filtrado.iterrows():
                print(f"Clase: {names[int(row['class'])]}, Confianza: {row['confidence']:.2f}, "
                    f"Coordenadas: ({row['xmin']:.2f}, {row['ymin']:.2f}) -> ({row['xmax']:.2f}, {row['ymax']:.2f})")

            # Si se proporciona un ROI, filtrar detecciones fuera de rango
            if roi:
                x_min, y_min, x_max, y_max = roi
                print(f"\nFiltrando detecciones fuera del ROI: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
                df_filtrado = df_filtrado[
                    (df_filtrado['xmin'] >= x_min) & (df_filtrado['xmax'] <= x_max) &
                    (df_filtrado['ymin'] >= y_min) & (df_filtrado['ymax'] <= y_max)
                ]

                # Log: Detecciones después del filtrado por ROI
                print("\nDetecciones después del filtrado por ROI:")
                for _, row in df_filtrado.iterrows():
                    print(f"Clase: {names[int(row['class'])]}, Confianza: {row['confidence']:.2f}, "
                        f"Coordenadas: ({row['xmin']:.2f}, {row['ymin']:.2f}) -> ({row['xmax']:.2f}, {row['ymax']:.2f})")

            # Dibujar rectángulos en la imagen para cada detección filtrada
            for _, row in df_filtrado.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = names[int(row['class'])]
                confidence = row['confidence']

                # Dibujar el rectángulo
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                # Añadir texto con la clase y la confianza
                cv2.putText(
                    img, f"{class_name} {confidence:.2f}", 
                    (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                )

            # Convertir el índice de clase a nombre de clase
            df_filtrado['class_name'] = df_filtrado['class'].apply(lambda x: names[int(x)])

            return df_filtrado, img
        except Exception as e:
            print(f"Error al ejecutar el modelo: {e}")
            return None, None
