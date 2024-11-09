import cv2
import pandas as pd
from ultralytics import YOLO

def load_model(model_path):
    try:
        # Cargar el modelo YOLOv5 personalizado
        model = YOLO(model_path)
        model.export(format="ncnn")  # Exportar a formato NCNN
        ncnn_model = YOLO("yolo11n_ncnn_model")  # Cargar el modelo NCNN exportado
        return ncnn_model
    except Exception as e:
        print(f"Error al cargar el modelo: {e}")
        return None

def run_model(model, img_path_or_img, confianza_minima=0.2, roi=None):
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

        # Recorte de la imagen si se proporciona un ROI
        if roi:
            x_min, y_min, x_max, y_max = roi
            print(f"ROI definido: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
            
            # Validación de que las coordenadas estén dentro de los límites de la imagen
            if x_min < 0 or y_min < 0 or x_max > img.shape[1] or y_max > img.shape[0]:
                print("Error: Las coordenadas del ROI están fuera del rango de la imagen.")
                return None, None
            
            # Recortar la imagen
            img = img[y_min:y_max, x_min:x_max]

        # Ejecutar el modelo en la imagen o en la región recortada
        results = model(img)
        if not results:
            print("No se detectaron objetos.")
            return None, None

        # Obtener las detecciones
        detections = results[0].boxes.data.cpu().numpy()  # Obtener detecciones del primer resultado
        print("Detectados:", detections)
        names = model.names  # Obtener los nombres de las clases desde el modelo
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

# Simulación de ejecución del script
model_path = "yolo11n.pt"
model = load_model(model_path)

if model:
    # Simular una imagen cargada o proporcionar una ruta de imagen
    img_path = "calibracion/tablero-ajedrez-1.jpg"  # Reemplaza con la ruta de la imagen o usa una imagen cargada con cv2
    df, processed_img = run_model(model, img_path, confianza_minima=0.3, roi=(50, 50, 200, 200))

    if df is not None:
        print("DataFrame con detecciones filtradas:", df)
