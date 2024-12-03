import cv2
from ultralytics import YOLO
from picamera2 import Picamera2
import numpy as np
import serial
try:
    # Configuración del puerto serial
    serial_port = serial.Serial(
        port='/dev/ttyUSB0',  # Cambia esto según tu configuración
        baudrate=115200,
        timeout=1
    )
    
    # Enviar el comando para encender la luz
    serial_port.write(b"LED_ON\n")
    print("Comando 'LED_ON' enviado")

except Exception as e:
    print(f"Error al enviar el mensaje: {str(e)}")
# Cargar el modelo YOLO
# model = YOLO("best_yolo11n.pt")
model = YOLO("best_ncnn_model_yolo11n")
# model = YOLO("best.pt")  # Asegúrate de tener el modelo descargado

# Inicializar la cámara
picam2 = Picamera2()
camera_config = picam2.create_still_configuration({"size": (640, 480)})
picam2.configure(camera_config)
picam2.start()

while True:
    # Capturar un fotograma como un array numpy
    frame = picam2.capture_array("main")

    # Realizar la detección de objetos
    results = model(frame)

    # Mostrar los resultados en el fotograma
    annotated_frame = results[0].plot()  # Dibuja los cuadros delimitadores en el fotograma

    # Convertir el fotograma anotado a BGR para mostrarlo con OpenCV
    annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)

    # Mostrar el fotograma anotado
    cv2.imshow("YOLO Object Detection", annotated_frame_bgr)

    # Salir si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar los recursos
picam2.stop()
cv2.destroyAllWindows()
