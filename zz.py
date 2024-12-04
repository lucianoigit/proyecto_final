import customtkinter as ctk
import cv2
import numpy as np
from ultralytics import YOLO
from picamera2 import Picamera2
import serial
import threading
import json
import os
import PIL.Image
import PIL.ImageTk
import sys
import time

class ObjectDetectionApp:
    CONFIG_FILE = "config.json"

    def __init__(self, root):
        # Configuración de CustomTkinter
        ctk.set_appearance_mode("Dark")  
        ctk.set_default_color_theme("blue")

        # Configuraciones principales
        self.root = root
        self.root.title("Object Detection System")
        self.root.geometry("800x480")
        self.root.resizable(False, False)

        # Establecer un manejador de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Estados de control
        self.modelo_iniciado = False
        self.clasificacion_iniciada = False
        self.stop_event = threading.Event()

        # Configuración de recursos
        # Iniciar cámara
        self.picam2 = Picamera2()
        camera_config = self.picam2.create_still_configuration({"size": (640, 480)})
        self.picam2.configure(camera_config)
        self.picam2.start()

        # Cargar modelo YOLO
        self.model = YOLO("best_ncnn_model_yolo11n")

        self.serial_port = None

        self.procesar_imagen = True
        self.is_first_move = True

        # Almacenar referencias a hilos
        self.processing_threads = []

        # Estado para saber qué pantalla mostrar
        self.current_config_screen = "main"
        self.config_data = self.load_config()

        # Crear interfaz
        self.create_interface()

        self.iniciar_comunicacion_serial()

        cmd = "ADD_CATEGORY bottle,0,0,-600\n"
        print(cmd)
        self.serial_port.write(cmd.encode())
        # Esperar respuesta  del ESP32
        while True:
            respuesta = self.serial_port.readline().decode().strip()
            print(respuesta)
            if respuesta == "Categoría añadida":
                break

    def load_config(self):
        """Cargar configuraciones desde un archivo JSON."""
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as file:
                return json.load(file)
        return {"models": {}, "workspace_area": {}, "confidence": {}}

    def save_config(self):
        """Guardar configuraciones en un archivo JSON."""
        try:
            with open("config.json", "w") as file:
                json.dump(self.config_data, file, indent=4)
            print("Configuración guardada exitosamente.")
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")

    def create_interface(self):
        # Crear tab view
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        # Pestañas
        self.inicio_tab = self.tabview.add("Inicio")
        self.config_tab = self.tabview.add("Configuración")
        self.stats_tab = self.tabview.add("Estadísticas")

        # Configurar pestañas
        self.setup_inicio_tab()
        self.setup_config_tab()
        self.setup_stats_tab()



    # Inicio
    def setup_inicio_tab(self):
        # Frame de control
        self.control_frame = ctk.CTkFrame(self.inicio_tab)
        self.control_frame.pack(padx=10, pady=10, fill="x")

        # Botones de control
        self.btn_iniciar_modelo = ctk.CTkButton(
            self.control_frame, 
            text="Iniciar Modelo", 
            command=self.iniciar_modelo,
            fg_color="green",
        )
        self.btn_iniciar_modelo.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.btn_iniciar_clasificacion = ctk.CTkButton(
            self.control_frame, 
            text="Iniciar Clasificación", 
            command=self.iniciar_clasificacion,
            fg_color="blue",
            state="disabled"
        )
        self.btn_iniciar_clasificacion.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        self.btn_detener = ctk.CTkButton(
            self.control_frame, 
            text="Detener", 
            command=self.detener_todo,
            fg_color="red",
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=5, pady=5, expand=True, fill="x")

        # Frame para imágenes
        self.frame_container = ctk.CTkFrame(self.inicio_tab)
        self.frame_container.pack(padx=10, pady=10, fill="both", expand=True)

        # Etiquetas de frames
        self.original_frame_label = ctk.CTkLabel(self.frame_container, text="Frame Original")
        self.original_frame_label.grid(row=0, column=0, padx=5, pady=5)

        self.processed_frame_label = ctk.CTkLabel(self.frame_container, text="Frame Procesado")
        self.processed_frame_label.grid(row=0, column=1, padx=5, pady=5)

        # Contenedores de imágenes
        self.original_image_container = ctk.CTkLabel(self.frame_container, text="No hay imagen")
        self.original_image_container.grid(row=1, column=0, padx=5, pady=5)

        self.processed_image_container = ctk.CTkLabel(self.frame_container, text="No hay imagen")
        self.processed_image_container.grid(row=1, column=1, padx=5, pady=5)



    # Configuración
    def setup_config_tab(self):
        """Configurar la pestaña de configuración inicial."""
        # Frame principal
        self.config_main_frame = ctk.CTkFrame(self.config_tab)
        self.config_main_frame.pack(fill="both", expand=True)

        # Botones grandes
        self.btn_config_area = ctk.CTkButton(
            self.config_main_frame, 
            text="Configurar Área de Trabajo", 
            command=self.configure_area
        )
        self.btn_config_area.pack(pady=20)

        self.btn_config_model = ctk.CTkButton(
            self.config_main_frame, 
            text="Configurar Modelo de IA", 
            command=self.configure_model
        )
        self.btn_config_model.pack(pady=20)

        # Frame para configuraciones adicionales
        self.config_model_frame = ctk.CTkFrame(self.config_tab)


    # Configuración de área de trabajo
    def configure_area(self):
        """Configurar el área de trabajo mediante selección de puntos de referencia."""

        self.reference_points = []

        def open_camera_and_select_points():
            
            self.reference_points.clear()

            cv2.namedWindow("Seleccione cuatro puntos", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Seleccione cuatro puntos", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setMouseCallback("Seleccione cuatro puntos", mouse_callback)

            while True:
                frame = self.picam2.capture_array("main")
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Dibujar puntos seleccionados
                for point in self.reference_points:
                    cv2.circle(frame, point, 5, (0, 255, 0), -1)

                # Dibujar segmentos entre puntos seleccionados
                if len(self.reference_points) > 1:
                    for i in range(len(self.reference_points) - 1):
                        cv2.line(frame, self.reference_points[i], self.reference_points[i+1], (0, 255, 0), 2)
                
                # Dibujar centroide y guardar
                if len(self.reference_points) == 4:
                    
                    cv2.polylines(frame, [np.array(self.reference_points)], isClosed=True, color=(255, 0, 0), thickness=2)
                    
                    centroid = calculate_centroid(self.reference_points)
                    print("Centroide:", centroid)
                    cv2.circle(frame, centroid, 5, (0, 0, 255), -1)
                    
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, "Guardando...", (50, 50), font, 1, (0, 255, 255), 2, cv2.LINE_AA)

                    # Calcular escala de píxeles a milímetros
                    pixel_to_mm_scale = calculate_pixel_to_mm_scale(self.reference_points)

                    # Actualizar los puntos y el centroide en la configuración
                    self.config_data["workspace_area"]["vertices"] = [
                        {"x": point[0], "y": point[1]} for point in self.reference_points
                    ]
                    self.config_data["workspace_area"]["centroid"] = {"x": centroid[0], "y": centroid[1]}
                    self.config_data["workspace_area"]["pixel_to_mm_scale"] = pixel_to_mm_scale

                    # Guardar la configuración actualizada
                    self.save_config()
                    
                    cv2.imshow("Seleccione cuatro puntos", frame)
                    cv2.waitKey(2000)
                    break
                else:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame, 'Seleccione 4 puntos', (50, 50), font, 1, (0, 255, 255), 2, cv2.LINE_AA)

                cv2.imshow("Seleccione cuatro puntos", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cv2.destroyAllWindows()

        def mouse_callback(event, x, y, flags, param):
            """Manejar eventos del mouse."""
            if event == cv2.EVENT_LBUTTONDOWN:
                self.reference_points.append((x, y))
                print(f"Punto seleccionado: {x, y}")
                # cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                # cv2.imshow("Configuración de Área de Trabajo", frame)

        def calculate_centroid(points):
            """Calcula el centroide de un conjunto de puntos (vértices del polígono)."""
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            centroid_x = int(np.mean(x_coords))
            centroid_y = int(np.mean(y_coords))
            return (centroid_x, centroid_y)

        def calculate_pixel_to_mm_scale(points):
            """Calcula la relación de píxeles a milímetros."""
            # Distancias en píxeles entre los puntos consecutivos
            pixel_distances = []
            for i in range(4):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % 4]  # Siguiente punto (ciclo cerrado)
                distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                pixel_distances.append(distance)
            
            # Promedio de las distancias en píxeles
            avg_pixel_distance = np.mean(pixel_distances)

            # Relación de escala (200 mm / distancia promedio en píxeles)
            return 200.0 / avg_pixel_distance
    
        open_camera_and_select_points()
        print("Puntos de referencia seleccionados:", self.reference_points)
        print("Relación píxeles a milímetros:", self.config_data["workspace_area"]["pixel_to_mm_scale"])
        
        # if(len(self.reference_points) == 4):
        #     cv2.polylines(frame, [np.array(self.reference_points)], isClosed=True, color=(255, 0, 0), thickness=2)
        #     cv2.imshow("Configuración de Área de Trabajo", frame)
        #     cv2.waitKey(0)
            # self.calculate_scale_factor()
        
        # Lógica para dibujar el área de interés en el stream de la cámara.
        # print("Configurar área de trabajo: Aquí se mostraría el stream para seleccionar el área.")

    def calculate_scale_factor(self, reference_size=(200,200)):
        """
        Calcular el factor de escala para convertir pixeles a milímetros.
        
        :param reference_size: Tamaño de referencia en mm (ancho, alto)
        """
        def point_distance(p1, p2):
            return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

        distance_px = [
            point_distance(self.reference_points[0], self.reference_points[1]),
            point_distance(self.reference_points[1], self.reference_points[2]),
            point_distance(self.reference_points[2], self.reference_points[3]),
            point_distance(self.reference_points[3], self.reference_points[0])
        ]

        # Mapeo de distancias de referencia
        ref_width, ref_height = reference_size
        expected_side_lengths = [ref_width, ref_height, ref_width, ref_height]

        scale_factors = [expected / mesure for expected, mesure in zip(expected_side_lengths, distance_px)]
        self.pixel_to_mm_factor = np.mean(scale_factors)

        print(f"Factor de escala (píxeles a mm): {self.pixel_to_mm_factor}")

    def convert_pixel_to_mm(self, pixel_point):
        """
        Convertir coordenadas de píxeles a milímetros.
        
        :param pixel_point: Punto en coordenadas de píxel
        :return: Punto en coordenadas de milímetros
        """
        if not hasattr(self, 'pixel_to_mm_factor'):
            raise ValueError("Primero debe calcular el factor de escala con configure_area()")
        
        return (
            pixel_point[0] * self.pixel_to_mm_factor,
            pixel_point[1] * self.pixel_to_mm_factor
        )



    # Configuración de modelo
    def configure_model(self):
        """Cambiar a la interfaz de configuración del modelo."""
        # self.switch_to_model_config()
        pass

    def switch_to_model_config(self):
        """Cambiar la visualización a la configuración del modelo."""
        self.config_main_frame.pack_forget()
        self.config_model_frame.pack(fill="both", expand=True)

        for widget in self.config_model_frame.winfo_children():
            widget.destroy()

        # Título
        title_label = ctk.CTkLabel(self.config_model_frame, text="Configuración del Modelo de IA", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Crear un frame para dividir la pantalla
        content_frame = ctk.CTkFrame(self.config_model_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)


        # Parte izquierda (Modelos y Clases)
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Seleccionar modelo
        model_names = list(self.config_data["models"].keys())
        self.model_var = ctk.StringVar(value=model_names[0])
        model_menu = ctk.CTkOptionMenu(
            self.config_model_frame, 
            values=model_names, 
            variable=self.model_var,
            command=self.update_model_classes
        )
        model_menu.pack(pady=10)

        # Frame para clases
        self.classes_frame = ctk.CTkFrame(left_frame)
        self.classes_frame.pack(pady=10)


        # Parte derecha (Confianza)
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Selección de confianza
        confidence_label = ctk.CTkLabel(self.config_model_frame, text="Confianza:")
        confidence_label.pack(pady=10)

        self.confidence_var = ctk.DoubleVar(value=self.config_data.get("confidence", 0.7))
        for value in [0.7, 0.8, 0.9]:
            confidence_button = ctk.CTkRadioButton(
                self.config_model_frame, 
                text=str(value), 
                variable=self.confidence_var, 
                value=value
            )
            # confidence_button.pack(side="left", padx=5)
            confidence_button.pack(anchor="w", padx=5)

        # Parte inferior (Botones)
        bottom_frame = ctk.CTkFrame(self.config_model_frame)
        bottom_frame.pack(fill="x", pady=10, padx=10)
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)
        
        # Botón para volver
        back_button = ctk.CTkButton(
            bottom_frame, 
            text="Volver", 
            command=self.switch_to_main_config
        )
        back_button.grid(row=0, column=0, sticky="w" , padx=10)
        # # Botón para volver
        # back_button = ctk.CTkButton(
        #     self.config_model_frame, 
        #     text="Volver", 
        #     command=self.switch_to_main_config
        # 
        # back_button.pack(pady=20)

        save_button = ctk.CTkButton(
            bottom_frame, 
            text="Guardar Configuración",
            command=self.save_model_config
        )
        back_button.grid(row=0, column=1, sticky="w" , padx=10)
        # save_button.pack(pady=10)
        # save_button = ctk.CTkButton(
        #     self.config_model_frame, 
        #     text="Guardar Configuración",
        #     command=self.save_model_config
        # )
        # save_button.pack(pady=10)


        # Actualizar clases del modelo inicial
        self.update_model_classes(self.model_var.get())

    def update_model_classes(self, model_name):
        """Actualizar las clases asociadas al modelo seleccionado."""
        for widget in self.classes_frame.winfo_children():
            widget.destroy()

        # Obtener clases del modelo
        model_data = self.config_data["models"].get(model_name, {})
        classes = model_data.get("classes", {})

        for cls, coords in classes.items():
            label = ctk.CTkLabel(self.classes_frame, text=f"Ubicación para {cls}:")
            label.pack(pady=5)

            # Entrada para X
            entry_x = ctk.CTkEntry(self.classes_frame, placeholder_text="X (mm)")
            entry_x.insert(0, str(coords["x"]) if coords["x"] is not None else "")
            entry_x.pack(pady=5)

            # Entrada para Y
            entry_y = ctk.CTkEntry(self.classes_frame, placeholder_text="Y (mm)")
            entry_y.insert(0, str(coords["y"]) if coords["y"] is not None else "")
            entry_y.pack(pady=5)

            # Guardar referencias para acceder más adelante
            self.config_data["models"][model_name]["classes"][cls]["entry_x"] = entry_x
            self.config_data["models"][model_name]["classes"][cls]["entry_y"] = entry_y

        # classes = self.config_data["models"].get(model_name, {}).get("classes", [])
        # for cls in classes:
        #     label = ctk.CTkLabel(self.classes_frame, text=f"Ubicación para {cls}:")
        #     label.pack(pady=5)

        #     entry_x = ctk.CTkEntry(self.classes_frame, placeholder_text="X (mm)")
        #     entry_x.pack(pady=5)
        #     entry_y = ctk.CTkEntry(self.classes_frame, placeholder_text="Y (mm)")
        #     entry_y.pack(pady=5)

    def save_model_config(self):
        """Guardar configuraciones del modelo."""
        selected_model = self.model_var.get()
        confidence = self.confidence_var.get()
        self.config_data["confidence"] = confidence

        # Guardar coordenadas de cada clase
        for cls, widgets in self.config_data["models"][selected_model]["classes"].items():
            entry_x = widgets["entry_x"]
            entry_y = widgets["entry_y"]
            widgets["x"] = float(entry_x.get()) if entry_x.get() else None
            widgets["y"] = float(entry_y.get()) if entry_y.get() else None

        # Guardar en archivo
        print(f"Configuración guardada para el modelo: {selected_model}")
        self.save_config()

    def switch_to_main_config(self):
        """Volver a la visualización principal de configuraciones."""
        self.config_model_frame.pack_forget()
        self.config_main_frame.pack(fill="both", expand=True)




    # Estadísticas
    def setup_stats_tab(self):
        # Placeholder para estadísticas futuras
        stats_label = ctk.CTkLabel(self.stats_tab, text="Estadísticas de detección próximamente")
        stats_label.pack(padx=20, pady=20)





    # Botones de control
    # def iniciar_modelo(self):
    #     try:
    #         # Habilitar botones
    #         self.btn_detener.configure(state="normal")
    #         self.btn_iniciar_modelo.configure(state="disabled")
            
    #         # Iniciar thread de captura y procesamiento
    #         self.stop_event.clear()
    #         thread = threading.Thread(target=self.capturar_y_procesar, daemon=True)
    #         thread.start()
    #         self.processing_threads.append(thread)
            
    #         self.modelo_iniciado = True
    #     except Exception as e:
    #         print("Error iniciar modelo")
    def iniciar_modelo(self):
        try:
            # Habilitar botones
            self.btn_detener.configure(state="normal")
            self.btn_iniciar_modelo.configure(state="disabled")
            
            # Iniciar thread de captura y procesamiento
            self.stop_event.clear()
            thread = threading.Thread(target=self.iniciar, daemon=True)
            thread.start()
            # thread_frame_left = threading.Thread(target=self.mostrar_imagen, args=(self.frame,), daemon=True)
            # thread_frame_left.start()
            self.processing_threads.append(thread)
            # self.processing_threads.append(thread_frame_left)
            
            self.modelo_iniciado = True
        except Exception as e:
            print("Error iniciar modelo")

    def iniciar_clasificacion(self):
        if not self.modelo_iniciado or self.clasificacion_iniciada:
            return
        
        self.stop_event.set()
        self.modelo_iniciado = False

        try:
            # Iniciar thread de clasificación
            self.stop_event.clear()
            thread = threading.Thread(target=self.clasificar_objetos, daemon=True)
            thread.start()
            self.processing_threads.append(thread)
            
            self.clasificacion_iniciada = True
        except Exception as e:
            print("Error iniciar clasificacion")

    def detener_todo(self):
        # Detener todos los procesos
        self.stop_event.set()
        
        # Resetear estados
        self.modelo_iniciado = False
        self.clasificacion_iniciada = False
        
        # Deshabilitar botones
        self.btn_iniciar_clasificacion.configure(state="disabled")
        self.btn_detener.configure(state="disabled")

    """    def iniciar_modelo(self):
        try:
            frame = self.picam2.capture_array("main")
            if self.model:
                results = self.model(frame)
                annotated_frame = frame.copy()

                # Filtrar resultados basados en la confianza del modelo
                filtered_results = self.filter_results_by_confidence(results)
                print(filtered_results)
                self.draw_workspace_area(annotated_frame)

                self.detected_objects_mm = []

                # Dibujar las cajas filtradas
                self.draw_filtered_boxes(annotated_frame, filtered_results)

                self.enviar_comandos(self.detected_objects_mm)
                
                # Convertir frames
                original_photo = self.convert_frame_to_photo(frame)
                processed_photo = self.convert_frame_to_photo(annotated_frame)

                self.root.after(10, self.update_frames, original_photo, processed_photo)

                # Esperar el comando "SEGUI" antes de procesar el siguiente frame
                while True:
                    respuesta = self.serial_port.readline().decode().strip()
                    if respuesta == "SEGUI":
                        print("Recibido 'SEGUI', procesando nuevo frame...")
                        break

        except Exception as e:
            print("Error iniciar modelo")
    """
    def iniciar(self):
        try:
            # # Iniciar hilo para esperar comandos del ESP32
            # threading.Thread(target=self.esperar_comandos, daemon=True).start()

            while not self.stop_event.is_set():
                frame = self.picam2.capture_array("main")
                original_photo = self.convert_frame_to_photo(frame)
                self.root.after(0, self.update_frame_left, original_photo)
                # Realizar nueva inferencia cuando se reciba "SEGUI"
                if self.procesar_imagen:
                    if self.model:
                        frame = self.picam2.capture_array("main")
                        results = self.model(frame)
                        annotated_frame = frame.copy()

                        # Filtrar resultados basados en la confianza del modelo
                        filtered_results = self.filter_results_by_confidence(results)
                        print(filtered_results)
                        self.draw_workspace_area(annotated_frame)

                        self.detected_objects_mm = []

                        # Dibujar las cajas filtradas
                        self.draw_filtered_boxes(annotated_frame, filtered_results)

                        if self.is_first_move:
                            self.is_first_move = False
                            # original_photo = self.convert_frame_to_photo(frame)
                            processed_photo = self.convert_frame_to_photo(annotated_frame)
                            self.root.after(0, self.update_frame_right, processed_photo)
                            # self.root.after(0, self.update_frames, original_photo, processed_photo)
                            self.enviar_comandos(self.detected_objects_mm)
                            # Iniciar hilo para esperar comandos del ESP32
                            hilo = threading.Thread(target=self.esperar_comandos, daemon=True)
                            hilo.start()
                            # self.detected_objects_mm.clear()
                            self.processing_threads.append(hilo)
                        # self.enviar_comandos(self.detected_objects_mm)

                        # Actualizar la lista compartida de objetos detectados
                        # self.objetos_detectados = self.detected_objects_mm
                        self.procesar_imagen = False  # Detener procesamiento hasta recibir "SEGUI"
                    
                        # Convertir frames
                        # original_photo = self.convert_frame_to_photo(frame)
                        processed_photo = self.convert_frame_to_photo(annotated_frame)

                        self.root.after(0, self.update_frame_right, processed_photo)
                        # self.root.after(10, self.update_frames, original_photo, processed_photo)

        except Exception as e:
            print("Error iniciar modelo:", e)

    def esperar_comandos(self):
        """Espera comandos del ESP32 y gestiona el flujo."""
        try:
            while not self.stop_event.is_set():
                # Leer comando del ESP32
                respuesta = self.serial_port.readline().decode().strip()

                if respuesta == "SEGUI":
                    # Habilitar procesamiento de nueva imagen
                    print(f"Comando recibido: {respuesta}")
                    self.procesar_imagen = True

                elif respuesta == "START":
                    # Enviar la lista de objetos detectados
                    print(f"Comando recibido: {respuesta}")
                    self.enviar_comandos(self.detected_objects_mm)
                    self.detected_objects_mm.clear()
        except Exception as e:
            print("Error al esperar comandos:", e)

    def enviar_comandos(self, objetos_detectados):
        """Envía objetos detectados al ESP32."""
        z = int(-600)
        try:
            if objetos_detectados:
                for i, objeto in enumerate(objetos_detectados):
                    if i==0:
                        cb = -200
                    else:
                        cb = 0
                    # cb = -200 if i == 0 else 0  # cb es -200 solo para el primer objeto, luego 0
                    comando = f"{objeto['x_mm']:.2f},{objeto['y_mm']:.2f},{z},{cb},{objeto['class_name']}\n"
                    print("Comando enviado:", comando)
                    self.serial_port.write(comando.encode())  # Enviar comando por serial
                    
                    # Esperar respuesta "OK" del ESP32
                    # print("Esperar respuesta 'OK'")
                    start_time = time.time()
                    while True:
                        if time.time() - start_time > 5:
                            raise serial.SerialTimeoutException("Tiempo de espera excedido")
                        
                        respuesta = self.serial_port.readline().decode().strip()
                        if respuesta == "OK":
                            print("Respuesta: ", respuesta)
                            break

                # Enviar comando "FIN" para indicar que se enviaron todos los objetos
                print("Comando FIN enviado")
                self.serial_port.write(b"FIN\n")
            else:
                # Caso sin objetos detectados
                comando = "0,0,0,-200,nada\n"
                print("Comando enviado:", comando)
                self.serial_port.write(comando.encode())  # Enviar comando por serial
                
                start_time = time.time()
                # Esperar respuesta "OK" del ESP32
                while True:
                    if time.time() - start_time > 5:
                        raise serial.SerialTimeoutException("Tiempo de espera excedido")
                    
                    respuesta = self.serial_port.readline().decode().strip()
                    print(respuesta)
                    if respuesta == "OK":
                        break

                # Enviar comando "FIN"
                print("Comando FIN enviado")
                self.serial_port.write(b"FIN\n")
        except (serial.SerialTimeoutException, Exception) as e:
            print("Error al enviar comandos:", e)

    # def mostrar_imagen(self, frame):
    #     while not self.stop_event.is_set():
    #         original_photo = self.convert_frame_to_photo(frame)
    #         self.root.after(0, self.update_frame_left, original_photo)
    #         # self.root.after(10, self.update_frames, original_photo, processed_photo)

    # Procesamiento
    def capturar_y_procesar(self):
        while not self.stop_event.is_set():
            try:
                # Capturar frame
                frame = self.picam2.capture_array("main")
                # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Procesar frame si hay modelo
                if self.model:
                    results = self.model(frame)
                    annotated_frame = frame.copy()

                    # Filtrar resultados basados en la confianza del modelo
                    filtered_results = self.filter_results_by_confidence(results)
                    # annotated_frame = results[0].plot()

                    self.draw_workspace_area(annotated_frame)

                    # Dibujar las cajas filtradas
                    self.draw_filtered_boxes(annotated_frame, filtered_results)
                    
                    # Convertir frames
                    original_photo = self.convert_frame_to_photo(frame)
                    processed_photo = self.convert_frame_to_photo(annotated_frame)
                    
                    # Actualizar interfaz
                    self.root.after(10, self.update_frames, original_photo, processed_photo)
            
            except Exception as e:
                print(f"Error en captura y procesamiento: {e}")
                break

    def clasificar_objetos(self):
        while not self.stop_event.is_set():
            try:
                # Obtener frame
                frame = self.picam2.capture_array("main")
                # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Realizar detección
                if self.model:
                    results = self.model(frame)
                    annotated_frame = results[0].plot()
                    
                    # Convertir frames
                    original_photo = self.convert_frame_to_photo(frame)
                    processed_photo = self.convert_frame_to_photo(annotated_frame)
                    
                    # Actualizar interfaz
                    self.root.after(10, self.update_frames, original_photo, processed_photo)

                    # Filtrar resultados y preparar objetos para enviar
                    objetos_detectados = []  # Aquí debes llenar con los objetos detectados
                    for result in results[0].boxes.data.tolist():
                        x, y, z, w, nombre = result  # Asumiendo que tienes estas variables
                        objetos_detectados.append({'x': x, 'y': y, 'z': z, 'w': w, 'nombre': nombre})

                    # Enviar comandos si hay objetos detectados
                    if objetos_detectados:
                        self.enviar_comandos(objetos_detectados)

                # Esperar comando "START" para reiniciar el proceso
                while True:
                    respuesta = self.serial_port.readline().decode().strip()
                    if respuesta == "START":
                        break

            except Exception as e:
                print(f"Error en clasificación: {e}")
                break

    def iniciar_comunicacion_serial(self):
        try:
            # Configurar puerto serial
            self.serial_port = serial.Serial(
                port='/dev/ttyUSB0',
                baudrate=115200,
                timeout=1
            )
            self.serial_port.write(b"LED_ON\n")
        except Exception as e:
            print("Error al iniciar comunicacion serial")
    """
    def enviar_comandos(self, objetos_detectados):
        
        z = -600
        cb = -200
        if objetos_detectados:
            print("OBJETO DETECTADO")
            for i, objeto in enumerate(objetos_detectados):
                cb = -200 if i==0 else 0

                # Create the command string
                comando = f"{objeto['x_mm']},{objeto['y_mm']},{z},{cb},{objeto['class_name']}\n"
                print(comando)
                # Send the command over serial
                # self.serial_port.write(comando.encode())
                
                print("Esperar respuesta 'OK'")
                # Wait for response "OK"
                # while True:
                #     respuesta = self.serial_port.readline().decode().strip()
                #     if respuesta == "OK":
                #         break
            
            # Send command "FIN" after all objects have been sent
            # self.serial_port.write(b"FIN\n")
            print("FIN\n")
        else:
            print("OBJETO NO DETECTADO")
            # If no objects are detected, send default values
            default_command = "0,0,0,-200,nada\n"
            print(default_command)
            # self.serial_port.write(default_command.encode())
            
            print("Esperar respuesta 'OK'")
            # while True:
            #     respuesta = self.serial_port.readline().decode().strip()
            #     if respuesta == "OK":
            #         break
            print("FIN\n")

        # Wait for response "SEGUI" from ESP32 before proceeding
        while True:
            respuesta = self.serial_port.readline().decode().strip()
            if respuesta == "SEGUI":
                break

        # if objetos_detectados:
        #     for objeto in objetos_detectados:
        #         comando = f"{objeto['x_mm']},{objeto['y_mm']},-600,{cb},{objeto['class_name']}\n"
        #         print(comando)
        #         # self.serial_port.write(comando.encode())
                
        #         print("Esperar respuesta 'OK'")
        #         # # Esperar respuesta "OK"
        #         # while True:
        #         #     respuesta = self.serial_port.readline().decode().strip()
        #         #     if respuesta == "OK":
        #         #         break
                
        #     # Enviar comando "FIN"
        #     self.serial_port.write(b"FIN\n")
        # else:
        #     print("0,0,0,-200,nada\n")
        #     print("Esperar respuesta 'OK'")
        #     print("FIN\n")
        #     # Esperar respuesta "OK"
        #     # while True:
        #     #     respuesta = self.serial_port.readline().decode().strip()
        #     #     if respuesta == "OK":
        #     #         print("FIN\n")
        #     #         break
        #     # return
            
        
        # # Esperar respuesta "SEGUI"
        # while True:
        #     respuesta = self.serial_port.readline().decode().strip()
        #     if respuesta == "SEGUI":
        #         break
    """
    # Función para filtrar resultados por confianza
    def filter_results_by_confidence(self, results):
        """Filtrar los resultados según el umbral de confianza configurado en el archivo JSON."""
        filtered_results = []
        confidence_threshold = self.config_data["confidence"]  # Umbral de confianza desde el archivo JSON
        # confidence_threshold = self.config_data.get("confidence", 0.8)  # Umbral de confianza desde el archivo JSON

        for result in results[0].boxes.data:
            confidence = result[4]  # La confianza está en el índice 4 de cada resultado
            # class_id = int(result[5]) # El ID de la clase está en el índice 5
            if confidence >= confidence_threshold:
                filtered_results.append(result)
                # filtered_results.append({
                #     "x1": result[0],
                #     "y1": result[1],
                #     "x2": result[2],
                #     "y2": result[3],
                #     "confidence": confidence,
                #     "class_id": class_id
                # })
        
        return filtered_results

    # Función para dibujar el área de trabajo en el frame procesado
    def draw_workspace_area(self, frame):
        """Dibujar el área de trabajo en el frame usando los vértices guardados en el archivo JSON."""
        vertices = self.config_data["workspace_area"].get("vertices", [])
        if len(vertices) == 4:
            points = [(vertex["x"], vertex["y"]) for vertex in vertices]
            points = np.array(points, np.int32)
            points = points.reshape((-1, 1, 2))
            cv2.polylines(frame, [points], isClosed=True, color=(255, 255, 255), thickness=2)  # Dibuja en azul

    # Función para dibujar las cajas filtradas
    def draw_filtered_boxes(self, frame, filtered_results):
        """Dibuja las cajas de delimitación filtradas en el frame, con colores basados en su posición."""
        # Obtener el centroide del área de trabajo y la escala de conversión
        centroid_x = self.config_data["workspace_area"]["centroid"]["x"]
        centroid_y = self.config_data["workspace_area"]["centroid"]["y"]
        pixel_to_mm_scale = self.config_data["workspace_area"]["pixel_to_mm_scale"]
        class_name = "bottle"

        for result in filtered_results:
            x1, y1, x2, y2 = map(int, result[:4])  # Coordenadas de la caja
            confidence = result[4]  # Confianza de la predicción
            
            # Calcular el centro de la caja
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            is_inside = self.is_point_inside_workspace(center_x, center_y)

            # Verificar si la caja está dentro del área de trabajo
            # is_inside = self.is_box_inside_workspace(x1, y1, x2, y2)

            # Colorear la caja según si está dentro o fuera del área de trabajo
            box_color = (0, 255, 0) if is_inside else (255, 255, 0)  # Verde si está dentro, rojo si está fuera
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Opcional: Agregar texto con la confianza
            label = f"{class_name} ({confidence:.2f})"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

            # Imprimir el punto central si está dentro del área de trabajo
            if is_inside:
                # print(f"Punto central dentro del área de trabajo: ({center_x:.2f}, {center_y:.2f})")
                
                adjusted_x = center_x - centroid_x
                adjusted_y = center_y - centroid_y

                # Convertir coordenadas de píxeles a milímetros
                adjusted_x_mm = adjusted_x * pixel_to_mm_scale
                adjusted_y_mm = adjusted_y * pixel_to_mm_scale

                self.detected_objects_mm.append({
                    "x_mm": adjusted_x_mm,
                    "y_mm": adjusted_y_mm,
                    "confidence": confidence,
                    "class_name": class_name
                })

                print(f"Objeto detectado: {class_name}, Coordenadas (mm): ({adjusted_x_mm:.2f}, {adjusted_y_mm:.2f}), Confianza: {confidence:.2f}")
                # print(f"Punto central ajustado (mm): ({adjusted_x_mm:.2f}, {adjusted_y_mm:.2f})")

    # Función para verificar si la caja está dentro del área de trabajo
    def is_box_inside_workspace(self, x1, y1, x2, y2):
        """Verifica si una caja está completamente dentro del área de trabajo."""
        vertices = self.config_data["workspace_area"].get("vertices", [])
        if len(vertices) == 4:
            # Convertir los vértices en una lista de puntos
            points = [(vertex["x"], vertex["y"]) for vertex in vertices]

            # Crear un polígono a partir de los vértices del área de trabajo
            polygon = np.array(points, np.int32)
            polygon = polygon.reshape((-1, 1, 2))

            # Verificar si las esquinas de la caja están dentro del polígono
            box_points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            inside_count = 0

            for point in box_points:
                if cv2.pointPolygonTest(polygon, point, False) >= 0:  # Si el punto está dentro del área de trabajo
                    inside_count += 1

            # La caja está dentro del área de trabajo si todas sus esquinas están dentro
            return inside_count == 4
        return False      

    # Función para verificar si un punto está dentro del área de trabajo
    def is_point_inside_workspace(self, x, y):
        """Verifica si un punto (x, y) está dentro del área de trabajo."""
        vertices = self.config_data["workspace_area"].get("vertices", [])
        if len(vertices) == 4:
            # Convertir los vértices en una lista de puntos
            points = [(vertex["x"], vertex["y"]) for vertex in vertices]

            # Crear un polígono a partir de los vértices del área de trabajo
            polygon = np.array(points, np.int32)
            polygon = polygon.reshape((-1, 1, 2))

            # Usamos cv2.pointPolygonTest para comprobar si el punto está dentro del polígono
            return cv2.pointPolygonTest(polygon, (x, y), False) >= 0

        return False


    def convert_frame_to_photo(self, frame):
        # Convertir frame a formato PhotoImage
        imagen = PIL.Image.fromarray(frame)
        imagen = imagen.resize((320, 240), PIL.Image.LANCZOS)
        return PIL.ImageTk.PhotoImage(imagen)

    def update_frame_left(self, original_photo):
        # Actualizar frames en el hilo principal de Tkinter
        self.original_image_container.configure(image=original_photo)
        self.original_image_container.image = original_photo
        
    def update_frame_right(self, processed_photo):
        # Actualizar frames en el hilo principal de Tkinter
        self.processed_image_container.configure(image=processed_photo)
        self.processed_image_container.image = processed_photo

    def update_frames(self, original_photo, processed_photo):
        # Actualizar frames en el hilo principal de Tkinter
        self.original_image_container.configure(image=original_photo)
        self.original_image_container.image = original_photo
        
        self.processed_image_container.configure(image=processed_photo)
        self.processed_image_container.image = processed_photo

    def on_closing(self):
        # Detener todos los procesos
        self.detener_todo()
        
        # Esperar a que terminen los hilos
        for thread in self.processing_threads:
            thread.join(timeout=2)
        
        # Cerrar la aplicación
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

def main():
    root = ctk.CTk()
    app = ObjectDetectionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()