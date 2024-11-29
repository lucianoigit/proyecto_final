import cv2
import numpy as np
from picamera2 import Picamera2
from ultralytics import YOLO
import pandas as pd

def main():
    try:
        # Inicializar la cámara
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
        picam2.start()

        print("Cámara inicializada. Presiona 'q' para salir.")

        # Cargar el modelo YOLO
        model_path = "best_ncnn_model"  # Ruta al modelo
        model = YOLO(model_path)

        while True:
            # Capturar imagen de la cámara
            frame = picam2.capture_array()
            if frame is None or frame.size == 0:
                print("Error al capturar la imagen.")
                continue

            # Procesar la imagen con el modelo
            print("Procesando la imagen...")
            results = model(frame)
            detections = results[0].boxes.data.cpu().numpy()  # Obtener detecciones del primer resultado

            # Convertir detecciones en un DataFrame para facilidad de uso
            df = pd.DataFrame(detections, columns=['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class'])
            names = model.names  # Obtener los nombres de las clases

            # Log de detecciones
            if not df.empty:
                df['class_name'] = df['class'].apply(lambda x: names[int(x)])
                print("\nDetecciones:")
                print(df[['class_name', 'confidence', 'xmin', 'ymin', 'xmax', 'ymax']])
            else:
                print("No se detectaron objetos.")

            # Dibujar rectángulos en la imagen
            for _, row in df.iterrows():
                xmin, ymin, xmax, ymax = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                class_name = row['class_name']
                confidence = row['confidence']

                # Dibujar el rectángulo
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                # Añadir texto con la clase y confianza
                cv2.putText(frame, f"{class_name} {confidence:.2f}", 
                            (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Mostrar la imagen procesada
            cv2.imshow("Detecciones", frame)

            # Presiona 'q' para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
    finally:
        # Liberar recursos
        picam2.stop()
        cv2.destroyAllWindows()
        print("Recursos liberados. Fin del programa.")

if __name__ == "__main__":
    main()
