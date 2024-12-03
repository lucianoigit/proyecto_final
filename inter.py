import customtkinter as ctk
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageTk
import threading
import io
import time
import cv2

class YOLORealtimeDetection:
    def __init__(self):
        # Configuración de la ventana principal
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.window = ctk.CTk()
        self.window.title("Detección YOLO en Tiempo Real")
        self.window.geometry("800x480")
        
        # Variables de estado
        self.yolo_model = None
        self.camera_running = False
        self.capture_thread = None
        
        # Inicializar Picamera2
        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(
            main={"size": (640, 480)},
            lores={"size": (640, 480)}
        )
        self.picam2.configure(config)
        
        # Crear widgets
        self.create_widgets()
        
        # Cargar modelo YOLO
        self.load_yolo_model()
        
    def create_widgets(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True)
        
        # Botón para iniciar/detener detección
        self.detect_btn = ctk.CTkButton(
            self.main_frame, 
            text="Iniciar Detección", 
            command=self.toggle_detection,
            width=200
        )
        self.detect_btn.pack(pady=10)
        
        # Label para mostrar imagen/resultados
        self.imagen_label = ctk.CTkLabel(
            self.main_frame, 
            text="Esperando iniciar detección...",
            font=("Helvetica", 14)
        )
        self.imagen_label.pack(expand=True, fill="both", padx=10, pady=10)
        
    def load_yolo_model(self):
        try:
            # Cargar modelo YOLO
            self.yolo_model = YOLO("best_ncnn_model_yolo11n")
            print("Modelo YOLO cargado exitosamente")
        except Exception as e:
            print(f"Error al cargar modelo YOLO: {str(e)}")
            self.imagen_label.configure(text=f"Error al cargar modelo: {str(e)}")
        
    def toggle_detection(self):
        if not self.camera_running:
            self.start_detection()
        else:
            self.stop_detection()
        
    def start_detection(self):
        if not self.yolo_model:
            print("Modelo YOLO no cargado")
            return
        
        self.camera_running = True
        self.detect_btn.configure(text="Detener Detección")
        
        # Iniciar cámara
        self.picam2.start()
        
        # Iniciar captura en un hilo separado
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.capture_thread.start()
        
    def stop_detection(self):
        self.camera_running = False
        if self.capture_thread:
            self.capture_thread.join()
        
        # Detener cámara
        self.picam2.stop()
        
        self.detect_btn.configure(text="Iniciar Detección")
        self.imagen_label.configure(text="Detección detenida")
    
    def capture_frames(self):
        try:
            while self.camera_running:
                # Capturar frame
                frame = self.picam2.capture_array()
                
                # Realizar inferencia con YOLO
                results = self.yolo_model(frame, stream=True, verbose=False)
                
                # Dibujar recuadros y etiquetas
                for result in results:
                    boxes = result.boxes
                    
                    for box in boxes:
                        # Obtener coordenadas del cuadro delimitador
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Obtener clase y confianza
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        label = f"{self.yolo_model.names[cls]} {conf:.2f}"
                        
                        # Dibujar rectángulo y etiqueta solo si la confianza es > 0.5
                        if conf > 0.5:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, label, (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                # Convertir frame a formato RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Crear imagen PIL
                imagen_pil = Image.fromarray(frame_rgb)
                
                # Convertir a ImageTk
                imagen_tk = ImageTk.PhotoImage(imagen_pil)
                
                # Actualizar imagen en el hilo principal
                self.window.after(0, self.update_image, imagen_tk)
                
                # Pequeño retardo para controlar la velocidad de procesamiento
                time.sleep(0.01)
        
        except Exception as e:
            print(f"Error en detección: {str(e)}")
            self.window.after(0, self.handle_error, str(e))
        
        finally:
            self.camera_running = False
            self.window.after(0, self.reset_ui)
    
    def update_image(self, imagen):
        self.imagen_label.configure(image=imagen)
        self.imagen_label.image = imagen  # Mantener una referencia
    
    def handle_error(self, mensaje):
        self.imagen_label.configure(text=f"Error: {mensaje}")
        self.stop_detection()
    
    def reset_ui(self):
        self.detect_btn.configure(text="Iniciar Detección")
        self.imagen_label.configure(text="Detección detenida")
    
    def run(self):
        self.window.mainloop()

# Iniciar aplicación
if __name__ == "__main__":
    app = YOLORealtimeDetection()
    app.run()