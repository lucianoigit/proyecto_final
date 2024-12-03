import customtkinter as ctk
import cv2
import os
from PIL import Image, ImageTk
from picamera2 import Picamera2
import threading
from queue import Queue
import time
from datetime import datetime
import numpy as np
import serial

class CameraApp:
    def __init__(self):
        # Configurar el escalado DPI
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configuración inicial de la ventana
        self.root = ctk.CTk()
        self.root.title("Captura de Imágenes para Dataset")
        
        # Obtener el factor de escalado de la pantalla
        self.scale_factor = self.root.winfo_fpixels('1i') / 72
        
        # Ajustar el tamaño de la ventana según el escalado
        window_width = int(1200 * self.scale_factor)
        window_height = int(800 * self.scale_factor)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Tamaño objetivo para las imágenes en la UI
        self.display_size = (640, 640)
        
        # Variables de control
        self.is_running = True
        self.current_image = None
        self.base_dir = "/home/raspberrypi/proyecto_final/dataset"
        self.frame_queue = Queue(maxsize=2)
        self.camera_lock = threading.Lock()
        
        # Configuración de la interfaz (debe ir antes de init_camera para que status_label exista)
        self.setup_ui()
        
        # Inicialización de la cámara
        self.init_camera()
        
        # Iniciar el hilo de captura
        self.capture_thread = threading.Thread(target=self.camera_capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        # Iniciar la actualización de la interfaz
        self.update_ui()

        try:
            # Configuración del puerto serial
            self.serial_port = serial.Serial(
                port='/dev/ttyUSB0',  # Cambia esto según tu configuración
                baudrate=115200,
                timeout=1
            )
            
            # Enviar el comando para encender la luz
            self.serial_port.write(b"LED_ON\n")
            print("Comando 'LED_ON' enviado")
        
        except Exception as e:
            print(f"Error al enviar el mensaje: {str(e)}")

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal responsivo
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Frame izquierdo para controles (Scrollable)
        left_frame = ctk.CTkScrollableFrame(self.main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Entrada para el nombre del objeto
        ctk.CTkLabel(left_frame, text="Nombre del Objeto:").pack(pady=5)
        self.object_name = ctk.CTkEntry(left_frame)
        self.object_name.pack(pady=5, padx=10, fill="x")
        
        # Controles de la cámara
        ctk.CTkLabel(left_frame, text="Controles de Cámara").pack(pady=10)
        
        # Agregar controles deslizantes (repetir para cada control)
        
        
        # Otras configuraciones (balance de blancos, resolución, etc.)
        # ctk.CTkLabel(left_frame, text="Balance de Blancos Automático:").pack(pady=2)
        # self.awb_checkbox = ctk.CTkCheckBox(
        #     left_frame, text="Activar", command=self.toggle_awb
        # )
        # self.awb_checkbox.select()
        # self.awb_checkbox.pack(pady=5, padx=10, fill="x")
        
        # ctk.CTkLabel(left_frame, text="Modo de Balance de Blancos:").pack(pady=2)
        # self.awb_mode_menu = ctk.CTkOptionMenu(
        #     left_frame, 
        #     values=["auto", "incandescent", "fluorescent", "daylight", "cloudy"],
        #     command=self.change_awb_mode
        # )
        # self.awb_mode_menu.set("auto")
        # self.awb_mode_menu.pack(pady=5, padx=10, fill="x")
        
        # ctk.CTkLabel(left_frame, text="Resolución:").pack(pady=2)
        self.resolution_var = ctk.StringVar(value="640x480")
        # resolutions = ["640x480", "1280x720", "1920x1080"]
        # self.resolution_menu = ctk.CTkOptionMenu(
        #     left_frame, 
        #     values=resolutions,
        #     variable=self.resolution_var,
        #     command=self.change_resolution
        # )
        # self.resolution_menu.pack(pady=5, padx=10, fill="x")
        
        # Botón de captura
        self.capture_button = ctk.CTkButton(
            left_frame, 
            text="Capturar Imagen",
            command=self.capture_image
        )
        self.capture_button.pack(pady=20, padx=10, fill="x")
        
        # Frame derecho para visualización
        right_frame = ctk.CTkFrame(self.main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Área de visualización de la cámara
        self.camera_label = ctk.CTkLabel(right_frame)
        self.camera_label.pack(pady=10, fill="both", expand=True)
        
        # Área para mostrar la imagen capturada
        self.capture_label = ctk.CTkLabel(right_frame, text="")
        self.capture_label.pack(pady=10, fill="both", expand=True)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(right_frame, text="Estado: Iniciando...")
        self.status_label.pack(pady=5)


    # Métodos para controles adicionales
    def update_contrast(self, value):
        """Actualiza el contraste de la cámara"""
        try:
            self.picam2.set_controls({"Contrast": int(value)})
            print(f"Contraste actualizado a: {value}")  # Impresión en consola
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar contraste: {str(e)}")

    def update_saturation(self, value):
        """Actualiza la saturación de la cámara"""
        try:
            self.picam2.set_controls({"Saturation": int(value)})
            print(f"Saturación actualizada a: {value}")  # Impresión en consola
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar saturación: {str(e)}")

    def update_sharpness(self, value):
        """Actualiza la nitidez de la cámara"""
        try:
            self.picam2.set_controls({"Sharpness": int(value)})
            print(f"Nitidez actualizada a: {value}")  # Impresión en consola
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar nitidez: {str(e)}")

    def update_iso(self, value):
        """Actualiza el ISO de la cámara"""
        try:
            # Convierte el valor de ISO en un rango adecuado
            iso_value = float(value) / 100
            self.picam2.set_controls({"AnalogueGain": iso_value})
            print(f"ISO actualizado a: {iso_value:.2f}")  # Impresión en consola con 2 decimales
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar ISO: {str(e)}")


    def toggle_awb(self):
        """Activa o desactiva el balance de blancos automático"""
        try:
            awb_enabled = self.awb_checkbox.get() == 1
            self.picam2.set_controls({"AwbEnable": awb_enabled})
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar AWB: {str(e)}")

    def change_awb_mode(self, mode):
        """Cambia el modo de balance de blancos"""
        try:
            self.picam2.set_controls({"AwbMode": mode})
        except Exception as e:
            self.status_label.configure(text=f"Error al cambiar AWB: {str(e)}")

    def init_camera(self):
        """Inicializa la cámara"""
        try:
            self.picam2 = Picamera2()
            self.camera_config = self.picam2.create_preview_configuration()
            self.camera_config = self.picam2.create_still_configuration(
                main={"size": (640, 480)})
            # self.camera_config = self.picam2.create_still_configuration(
            #     main={"size": (640, 480)},
            #     lores={"size": (320, 240)},
            #     display="lores"
            # )
            self.picam2.configure(self.camera_config)
            self.picam2.start()
            time.sleep(2)  # Dar tiempo a la cámara para inicializarse
            self.status_label.configure(text="Cámara iniciada correctamente")
        except Exception as e:
            print(f"Error al inicializar la cámara: {str(e)}")
            self.status_label.configure(text=f"Error al inicializar la cámara: {str(e)}")

    def resize_image_for_display(self, image):
        """Redimensiona la imagen para mostrar en la UI considerando el DPI"""
        target_width = int(self.display_size[0] * self.scale_factor)
        target_height = int(self.display_size[1] * self.scale_factor)
        
        img_width, img_height = image.size
        aspect_ratio = img_width / img_height
        
        if img_width > target_width or img_height > target_height:
            if aspect_ratio > 1:
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image

    def camera_capture_loop(self):
        """Loop principal de captura de la cámara"""
        while self.is_running:
            try:
                # Captura el frame de la cámara
                frame = self.picam2.capture_array()
                
                # Detección de bordes con Canny
                edges = cv2.Canny(frame, 100, 200)
                edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
                
                # Si la cola está llena, elimina el frame más antiguo
                if self.frame_queue.full():
                    self.frame_queue.get()
                
                # Agrega el frame procesado (detección de bordes) a la cola
                self.frame_queue.put(edges_rgb)
                
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                print(f"Error en captura: {str(e)}")
                time.sleep(0.1)

    # def camera_capture_loop(self):
        # """Loop principal de captura de la cámara"""
        # while self.is_running:
        #     try:
        #         frame = self.picam2.capture_array()
        #         # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
        #         if self.frame_queue.full():
        #             self.frame_queue.get()
                
        #         # self.frame_queue.put(frame_rgb)
        #         self.frame_queue.put(frame)
        #         time.sleep(0.03)  # ~30 FPS
                
        #     except Exception as e:
        #         print(f"Error en captura: {str(e)}")
        #         time.sleep(0.1)

    def update_ui(self):
        """Actualiza la interfaz de usuario con el último frame disponible"""
        if not self.frame_queue.empty():
            try:
                frame_rgb = self.frame_queue.get_nowait()
                image = Image.fromarray(frame_rgb)
                image = self.resize_image_for_display(image)
                photo = ImageTk.PhotoImage(image)
                self.camera_label.configure(image=photo)
                self.camera_label.image = photo
            except Exception as e:
                print(f"Error en actualización UI: {str(e)}")
        
        if self.is_running:
            self.root.after(30, self.update_ui)

    def capture_image(self):
        """Captura y guarda una imagen"""
        if not self.object_name.get():
            self.status_label.configure(text="Error: Ingrese un nombre de objeto")
            return
        
        try:
            object_dir = os.path.join(self.base_dir, self.object_name.get())
            os.makedirs(object_dir, exist_ok=True)
            
            existing_files = os.listdir(object_dir)
            next_number = len(existing_files) + 1
            
            frame = self.picam2.capture_array()
            
            filename = f"{next_number}.jpg"
            filepath = os.path.join(object_dir, filename)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(filepath, frame_rgb)
            
            # image = Image.fromarray(frame_rgb)
            image = Image.fromarray(frame)
            image = self.resize_image_for_display(image)
            photo = ImageTk.PhotoImage(image)
            self.capture_label.configure(image=photo)
            self.capture_label.image = photo
            
            self.status_label.configure(text=f"Imagen guardada: {filepath}")
            
        except Exception as e:
            self.status_label.configure(text=f"Error al capturar: {str(e)}")

    def update_brightness(self, value):
        """Actualiza el brillo de la cámara"""
        try:
            # Usamos un rango de -1 a 1 para brillo con Picamera2
            normalized_brightness = (float(value) - 50) / 50  # Mapear 0-100 a -1 a 1
            self.picam2.set_controls({"Brightness": normalized_brightness})
            print(f"Brightness actualizado a: {value}")  # Impresión en consola
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar brillo: {str(e)}")

    def update_exposure(self, value):
        """Actualiza la exposición de la cámara"""
        try:
            self.picam2.set_controls({"ExposureTime": int(value * 1000)})
            print(f"ExposureTime actualizado a: {value}")  # Impresión en consola
        except Exception as e:
            self.status_label.configure(text=f"Error al ajustar exposición: {str(e)}")

    def change_resolution(self, resolution):
        """Cambia la resolución de la cámara"""
        width, height = map(int, resolution.split('x'))
        try:
            self.picam2.stop()
            self.camera_config = self.picam2.create_still_configuration(
                main={"size": (width, height)},
                lores={"size": (width//2, height//2)},
                display="lores"
            )
            self.picam2.configure(self.camera_config)
            self.picam2.start()
            time.sleep(2)
        except Exception as e:
            self.status_label.configure(text=f"Error al cambiar resolución: {str(e)}")

    def run(self):
        """Inicia la aplicación"""
        try:
            self.root.mainloop()
        finally:
            self.is_running = False
            if hasattr(self, 'capture_thread'):
                self.capture_thread.join(timeout=1)
            if hasattr(self, 'picam2'):
                self.picam2.close()

def main():
    ctk.deactivate_automatic_dpi_awareness()
    app = CameraApp()
    app.run()

if __name__ == "__main__":
    main()