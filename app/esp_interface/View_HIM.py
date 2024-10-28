import customtkinter as ctk
from PIL import Image, ImageTk,ImageOps
import numpy as np
import time
import json
import os
import cv2
from picamera2 import Picamera2
from matplotlib import pyplot as plt
from app.abstracts.ITransport import TransportInterface
from app.abstracts.ICommunication import CommunicationInterface
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from app.abstracts.IProcessing import ProcessingInterface
import sys

from app.services.reports_service import ReportsService

class View(ctk.CTk):
    def __init__(self, communication_service: CommunicationInterface, processing_service: ProcessingInterface, reports_service: ReportsService,transport_service:TransportInterface,ser,picamera:Picamera2):
        super().__init__()
        self.title("Delta Robot")
        self.geometry("800x480")
        self.root = self  # Asegúrate de que root es la instancia de la ventana
        #self.resizable(False,False)
        self.communication_service = communication_service
        self.processing_service = processing_service
        self.reports_service = reports_service
        self.transport_service = transport_service
        self.mtx = None
        self.picam2 = picamera  # Almacenamos la cámara para uso futuro
        self.dist = None
        self.calibracion = False
        self.reports = []
        self.image = None
        self.conected = False
        self.x_center =None
        self.y_center = None
        self.offset = None
        self.isOpen = ser
        self.isDisponible = False
        self.image_resultado =  None
        self.df_filtrado = None
        self.image_resultado = None
        self.residue_list = None
        self.x1=None
        self.x2=None
        self.y1=None
        self.y2=None
        self.mmx = None
        self.mmy = None 
        self.square_size = 50 
        self.points = []
        

        # Paleta de colores aplicada
        self.bg_color = "#dbe7fc"  # Fondo principal
        self.btn_color = "#bcbefa"  # Color de los botones
        self.nav_color = "#ffffff"  # Fondo del menú de navegación
        self.img_frame_color = "#ffffff"  # Fondo del cuadro de imagen
        self.text_color = "#000000"  # Color del texto

        # Aplicar fondo principal
        self.configure(fg_color=self.bg_color)

        self.panels = {}
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(1, weight=1)  # Column for content
        self.grid_rowconfigure(0, weight=1)

        # Menú de navegación lateral
        nav_bar = ctk.CTkFrame(self, corner_radius=0, fg_color=self.bg_color)
        nav_bar.grid(row=0, column=0, sticky="ns", padx=10, pady=10)  # Ajustado a la izquierda (navegación lateral)

        # Botones de navegación para cambiar de sección
        connectivity_button = ctk.CTkButton(nav_bar, command=self.show_connectivity_panel,
                                            text="",  # Sin texto
                                            image=self.load_icon("icons/connectivity.png"),  # Imagen cargada
                                            width=150, height=50,
                                            fg_color=self.bg_color,  # Mismo color que el fondo
                                            border_color=self.btn_color,  # Color del borde
                                            border_width=2,  # Ancho del borde
                                            hover_color=self.img_frame_color,  # Color hover
                                            text_color=self.text_color)
        connectivity_button.grid(row=0, column=0, padx=10, pady=10)

        # Otros botones con el mismo estilo
        start_section_button = ctk.CTkButton(nav_bar, command=self.show_main_panel,
                                            text="", 
                                            image=self.load_icon("icons/start.png"),
                                            width=150, height=50,
                                            fg_color=self.bg_color,
                                            border_color=self.btn_color,
                                            border_width=2,
                                            hover_color=self.img_frame_color)
        start_section_button.grid(row=1, column=0, padx=10, pady=10)

        configure_button = ctk.CTkButton(nav_bar, command=self.show_configure_panel,
                                        text="", 
                                        image=self.load_icon("icons/settings.png"),
                                        width=150, height=50,
                                        fg_color=self.bg_color,
                                        border_color=self.btn_color,
                                        border_width=2,
                                        hover_color=self.img_frame_color)
        configure_button.grid(row=2, column=0, padx=10, pady=10)

        dashboard_button = ctk.CTkButton(nav_bar, command=self.show_dashboard,
                                        text="", 
                                        image=self.load_icon("icons/dashboard.png"),
                                        width=150, height=50,
                                        fg_color=self.bg_color,
                                        border_color=self.btn_color,
                                        border_width=2,
                                        hover_color=self.img_frame_color)
        dashboard_button.grid(row=3, column=0, padx=10, pady=10)

        close_button = ctk.CTkButton(nav_bar, 
                                    text="",
                                    image=self.load_icon("icons/close.png"),
                                    width=150, height=50,
                                    fg_color=self.bg_color,
                                    border_color=self.btn_color,
                                    border_width=2,
                                    hover_color=self.img_frame_color,
                                    command=self.close_application)
        close_button.grid(row=4, column=0, padx=10, pady=10)

        # Panel principal para el contenido
        main_panel = ctk.CTkFrame(self, fg_color=self.img_frame_color)
        main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)  # A la derecha del menú de navegación
        self.panels["main"] = main_panel

        main_panel.grid_columnconfigure(0, weight=1)
        main_panel.grid_rowconfigure(2, weight=1)

        # Crear botón de inicio y detener
        self.start_button = ctk.CTkButton(main_panel, text="", 
                                        command=self.on_start_button_clicked, 
                                        image=self.load_icon("icons/start.png"),
                                        fg_color=self.img_frame_color, 
                                        border_color=self.btn_color,              
                                        border_width=2,
                                        hover_color=self.bg_color,
                                        text_color=self.text_color)
        self.start_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.stop_button = ctk.CTkButton(main_panel, text="", 
                                        command=self.on_stop_button_clicked, 
                                        image=self.load_icon("icons/stop.png"),
                                        fg_color=self.img_frame_color, 
                                        border_width=2,
                                        border_color=self.btn_color,
                                        hover_color=self.bg_color,
                                        text_color=self.text_color)
        self.stop_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.stop_button.grid_remove()  # Inicialmente ocultamos el botón de detener



        # Botón de inicio de stream de cámara
        start_section_button = ctk.CTkButton(nav_bar, command=self.start_camera_stream,
                                             text="", image=self.load_icon("icons/start.png"), 
                                             width=150, height=50, fg_color=self.bg_color,
                                             border_color=self.btn_color, border_width=2,
                                             hover_color=self.img_frame_color)
        start_section_button.grid(row=1, column=0, padx=10, pady=10)

        # Panel principal para el contenido
        main_panel = ctk.CTkFrame(self, fg_color=self.img_frame_color)
        main_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.panels["main"] = main_panel

        # Área de imagen clasificada (donde se verá el stream de la cámara)
        self.image_label = ctk.CTkLabel(main_panel, text="Imagen clasificada aparecerá aquí", anchor="center", 
                                        fg_color=self.img_frame_color, text_color=self.text_color)
        self.image_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


        # Tabla para mostrar los últimos 5 artículos clasificados
        self.articles_frame = ctk.CTkScrollableFrame(main_panel, fg_color=self.img_frame_color)
        self.articles_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Configurar las columnas de la tabla
# Crear la tabla con formato estilo Excel
        headers = ["ID", "Nombre", "Categoría", "Confianza", "Fecha"]
        col_widths = [50, 100, 100, 100, 100]  # Definir los anchos de las columnas
        row_height = 30  # Altura fija para las filas

        # Configurar las columnas de la tabla estilo Excel
        for col, header in enumerate(headers):
            # Crear un frame con borde para cada celda de encabezado
            frame = ctk.CTkFrame(self.articles_frame, fg_color=self.img_frame_color, corner_radius=0)
            frame.grid(row=0, column=col, padx=1, pady=1, sticky="nsew")
            
            # Crear el label dentro del frame para mostrar el texto
            label = ctk.CTkLabel(frame,
                                text=header,
                                fg_color=self.nav_color,
                                text_color=self.btn_color,
                                corner_radius=0,
                                width=col_widths[col],
                                height=row_height,
                                anchor="center")  # Centrar el texto
            label.grid(sticky="nsew")  # Expandir el label dentro del frame

        # Aquí agregamos las filas de los artículos
        for row_num, article in enumerate(self.reports[-5:], start=1):
            article_data = [article['id'], article['nombre'], article['categoria'], article['confianza'], article['fecha']]
            for col_num, data in enumerate(article_data):
                # Crear un frame con borde para cada celda de datos
                frame = ctk.CTkFrame(self.articles_frame, fg_color=self.img_frame_color, corner_radius=0)
                frame.grid(row=row_num, column=col_num, padx=1, pady=1, sticky="nsew")
                
                # Crear el label dentro del frame para mostrar el dato
                cell = ctk.CTkLabel(frame,
                                    text=data,
                                    fg_color=self.nav_color,
                                    text_color=self.btn_color,
                                    corner_radius=0,
                                    width=col_widths[col_num],
                                    height=row_height,
                                    anchor="center")
                cell.grid(sticky="nsew")  # Expandir el label dentro del frame

                # Inicialmente llenamos la tabla
        self.update_articles_table()

        # Panel de conectividad
        connectivity_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        self.panels["connectivity"] = connectivity_panel

        connectivity_panel.grid_columnconfigure(0, weight=1)
        connectivity_panel.grid_rowconfigure(1, weight=1)

        self.message_entry = ctk.CTkEntry(connectivity_panel, width=200, placeholder_text="Escriba un mensaje...")
        self.message_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        send_button = ctk.CTkButton(connectivity_panel, text="Enviar", command=self.send_message, width=80, height=40, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        send_button.grid(row=0, column=1, padx=10, pady=10)

        self.text_box = ctk.CTkTextbox(connectivity_panel, height=300, fg_color="#3e3e3e", text_color="#ffffff")
        self.text_box.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        # Panel de informes con selección
        reports_panel = ctk.CTkFrame(self, fg_color=self.bg_color)  # Fondo principal aplicado
        reports_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.panels["reports"] = reports_panel

        reports_panel.grid_columnconfigure(1, weight=1)
        reports_panel.grid_rowconfigure(1, weight=1)

        # Menú de selección para cambiar entre lista, gráfico de torta y histograma
        self.view_options = ["Lista de Clasificación", "Gráfico de Torta", "Histograma"]
        self.selected_view = ctk.StringVar(value=self.view_options[0])  # Valor por defecto

        # Ajustamos tamaño y colores del menú de selección
        select_view_menu = ctk.CTkOptionMenu(reports_panel, values=self.view_options, 
                                            command=self.update_view, variable=self.selected_view,
                                            width=200, height=40,  # Ajuste del tamaño
                                            fg_color=self.btn_color,  # Color del botón
                                            text_color=self.text_color,  # Color del texto
                                            button_color=self.nav_color)  # Color del botón desplegable
        select_view_menu.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Marco para la lista de clasificación
        self.reports_scrollable_frame = ctk.CTkScrollableFrame(
            reports_panel, 
            fg_color=self.nav_color,  # Color de fondo ajustado
            width=400,  # Ancho ajustado
            height=300  # Alto ajustado
        )
        self.reports_scrollable_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Panel para los gráficos de estadísticas
        self.stats_panel = ctk.CTkFrame(reports_panel, fg_color=self.img_frame_color)  # Fondo ajustado
        self.stats_panel.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Paneles para estadísticas individuales
        self.total_residues_label = ctk.CTkLabel(self.stats_panel, text="", fg_color=self.btn_color, text_color=self.btn_color)
        self.total_residues_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.category_pie_chart = ctk.CTkLabel(self.stats_panel, text="", text_color=self.btn_color)
        self.category_pie_chart.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.daily_histogram = ctk.CTkLabel(self.stats_panel, text="", fg_color=self.btn_color, text_color=self.btn_color)
        self.daily_histogram.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

                # Panel de configuración con fondo blanco
        configure_panel = ctk.CTkFrame(self, fg_color=self.img_frame_color)  # Fondo blanco
        configure_panel.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.panels["configure"] = configure_panel

        # Configurar la cuadrícula para el panel de configuración
        configure_panel.grid_columnconfigure((0, 1), weight=1)
        configure_panel.grid_rowconfigure((0, 1), weight=1)

        # Botón de calibración de cámara
        calibration_button = ctk.CTkButton(configure_panel, text="Calibración de Cámara", 
                                        command=self.calibrate_camera_type, fg_color=self.nav_color, 
                                        hover_color="#a3a7d9", text_color=self.text_color)
        calibration_button.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Botón de calibración de modelo ML
        ml_model_button = ctk.CTkButton(configure_panel, text="Calibración de Modelo ML", 
                                        command=self.calibrate_ml_model, fg_color=self.nav_color, 
                                        hover_color="#a3a7d9", text_color=self.text_color)
        ml_model_button.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Botón de calibración de tipo de cámara


        # Botón de configuración de cinta transportadora
        conveyor_config_button = ctk.CTkButton(configure_panel, text="Configuración de Cinta Transportadora", 
                                            command=self.configure_conveyor, fg_color=self.btn_color, 
                                            hover_color="#a3a7d9", text_color=self.text_color)
        conveyor_config_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        # Ajustar las proporciones de las columnas y filas del grid
        for i in range(2):  # Ajustar el número según la cantidad de filas o columnas que necesites
            configure_panel.grid_columnconfigure(i, weight=1)
            configure_panel.grid_rowconfigure(i, weight=1)

        self.show_main_panel()
        #self.receive_data()

    def start_camera_stream(self):
        """
        Inicia el stream de la cámara y muestra la imagen en `image_label`.
        """
        # Configuración de la cámara
        self.picam2.preview_configuration.main.size = (640, 480)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.configure("preview")
        self.picam2.start()

        # Actualizar el stream en `image_label`
        self.update_camera_stream()

    def update_camera_stream(self):
        """
        Captura un frame de la cámara, dibuja el cuadrado del área de trabajo y lo muestra en `image_label`.
        """
        # Captura el frame actual desde la cámara
        frame_rgb = self.picam2.capture_array()
        
        # Convertir el frame de RGB a BGR para usar con OpenCV
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        # Dibujar el cuadrado del área de trabajo en el frame
        if all(v is not None for v in [self.x1, self.y1, self.x2, self.y2]):
            start_point = (self.x1, self.y1)
            end_point = (self.x2, self.y2)
            color = (0, 255, 0)  # Verde
            thickness = 2  # Grosor del borde del cuadrado
            cv2.rectangle(frame_bgr, start_point, end_point, color, thickness)
        
        # Convertir el frame de nuevo a RGB para mostrar en Tkinter
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(frame_pil)

        # Actualizar el label de imagen con el nuevo frame
        self.image_label.configure(image=frame_tk)
        self.image_label.image = frame_tk  # Guardar referencia para evitar garbage collection

        # Programar la próxima actualización del frame
        self.after(30, self.update_camera_stream)  # 30 ms = ~30 fps

    def update_articles_table(self):
        # Limpiar filas anteriores
        for widget in self.articles_frame.winfo_children()[5:]:  # Ignoramos las primeras 5 que son los headers
            widget.destroy()

        # Obtener los últimos 5 artículos
        last_five_articles = self.reports[-5:] if len(self.reports) > 5 else self.reports

        # Mostrar artículos en la tabla
        for row_num, article in enumerate(last_five_articles, start=1):
            article_data = [article['id'], article['nombre'], article['categoria'], article['confianza'], article['fecha']]
            for col_num, data in enumerate(article_data):
                label = ctk.CTkLabel(self.articles_frame, text=data, fg_color=self.img_frame_color, text_color=self.text_color)
                label.grid(row=row_num, column=col_num, padx=5, pady=5, sticky="ew")

    def change_image_to_white(image):
        # Convierte la imagen a escala de grises y luego la colorea de blanco
        return ImageOps.colorize(image.convert('L'), black="white", white="white")
    
    # Funciones para manejar la lógica de los botones
    def on_start_button_clicked(self):
        # Lógica para iniciar el proceso
        self.start_process()

        # Ocultar el botón de inicio y mostrar el de detener
        self.start_button.grid_remove()
        self.stop_button.grid()

    def on_stop_button_clicked(self):
        # Lógica para detener el proceso
        self.stop_process()

        # Ocultar el botón de detener y mostrar el de inicio nuevamente
        self.stop_button.grid_remove()
        self.start_button.grid()

    def calibrate_camera_type(self):
        calibration_window = ctk.CTkToplevel(self)
        calibration_window.title("Configuración de Calibración")
        calibration_window.geometry("400x300")

        # Entradas de datos de calibración
        square_size_label = ctk.CTkLabel(calibration_window, text="Tamaño del cuadrado:")
        square_size_label.pack(pady=10)
        square_size_entry = ctk.CTkEntry(calibration_window)
        square_size_entry.pack(pady=5)

        # Botón para abrir la cámara y seleccionar puntos
        select_points_button = ctk.CTkButton(calibration_window, text="Seleccionar Puntos en Cámara",
                                             command=lambda: self.open_camera_and_select_points())
        select_points_button.pack(pady=10)

        # Botón para iniciar calibración con puntos seleccionados
        start_button = ctk.CTkButton(calibration_window, text="Iniciar Calibración", 
                                     command=lambda: self.start_calibration(square_size_entry))
        start_button.pack(pady=10)

    def open_camera_and_select_points(self):
        self.points.clear()  # Reiniciar la lista de puntos

        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(self.points) < 4:
                self.points.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                cv2.imshow("Seleccione cuatro puntos", frame)
                if len(self.points) == 4:
                    cv2.destroyWindow("Seleccione cuatro puntos")

        self.picam2.configure(self.picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"}))
        self.picam2.start()

        while True:
            frame = self.picam2.capture_array()
            for point in self.points:
                cv2.circle(frame, point, 5, (255, 0, 0), -1)

            if len(self.points) == 4:
                ordered_points = self.ordenar_puntos(self.points)
                cv2.polylines(frame, [np.array(ordered_points)], isClosed=True, color=(0, 255, 0), thickness=2)

            cv2.imshow("Seleccione cuatro puntos", frame)
            cv2.setMouseCallback("Seleccione cuatro puntos", click_event)

            if cv2.waitKey(1) & 0xFF == ord('q') or len(self.points) == 4:
                break

        self.picam2.stop()
        cv2.destroyAllWindows()

    def start_calibration(self, square_size_entry):
        if len(self.points) == 4:
            try:
                square_size = int(square_size_entry.get())
                x1, y1 = self.points[0]
                x2, y2 = self.points[2]
                self.calibrate_camera(square_size, x1=x1, y1=y1, x2=x2, y2=y2)
            except ValueError:
                print("Por favor, ingrese un tamaño de cuadrado válido.")
        else:
            print("Por favor, seleccione exactamente 4 puntos.")

    def ordenar_puntos(self, puntos):
        centroid = (sum([p[0] for p in puntos]) / len(puntos), sum([p[1] for p in puntos]) / len(puntos))
        return sorted(puntos, key=lambda p: np.arctan2(p[1] - centroid[1], p[0] - centroid[0]))


        
    def load_icon(self, path, hover=False):
        # Obtener la ruta base correcta dependiendo de si el script está empaquetado por PyInstaller o no
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, path)
        try:
            # Cargar la imagen y ajustar el tamaño según sea necesario
            image = Image.open(icon_path).resize((50, 50))
            if hover:
                # Cambiar el color de la imagen a blanco cuando hover=True
                image = change_image_to_white(image)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error cargando el icono en {path}: {e}")
            return None
        
    def show_main_panel(self):
        self.hide_all_panels()
        self.panels["main"].grid()
        self.panels["main"].tkraise()

    def show_configure_panel(self):
        self.hide_all_panels()
        self.panels["configure"].grid()
        self.panels["configure"].tkraise()

    def show_reports_panel(self):
        self.hide_all_panels()
        self.panels["reports"].grid()
        self.panels["reports"].tkraise()
        self.update_reports()

    def show_connectivity_panel(self):
        self.hide_all_panels()
        self.panels["connectivity"].grid()
        self.panels["connectivity"].tkraise()

    def hide_all_panels(self):
        for panel in self.panels.values():
            panel.grid_remove()



    def send_message(self):
        data = self.message_entry.get()
        if data:
            self.communication_service.send_message(data)
            print(f"Mensaje enviado: {data}")
            self.message_entry.delete(0, ctk.END)

    def start_process(self):
        self.clasificacion()

    def stop_process(self):
        pass



    def calibrate_ml_model(self):
        # Lógica para calibración de modelo ML
        pass

    def configure_conveyor(self):
        # Lógica para configuración de cinta transportadora
        pass


    def show_dashboard(self):
        self.show_reports_panel()

    def close_application(self):
        self.quit()

    def iniciar_clasificacion(self):
        if self.isOpen is  None:
            print("Entramos a la clasificación")

            if self.df_filtrado is None or self.df_filtrado.empty:
                
                # Definimos la función de captura en segundo plano
                def capture_image_in_background():
                    # Clasificamos en segundo plano
                    img = self.processing_service.capture_image()
                    
                    # Verificar si la imagen fue capturada correctamente
                    if img is None:
                        print("Error: No se pudo capturar la imagen.")
                        self.root.after(500, self.iniciar_clasificacion)  # Asegurarse de que invoque el método correcto
                        return

                    try:
                        img_undistorted = self.processing_service.undistorted_image(img)
                        
                        # Continuamos con la lógica después de capturar y procesar la imagen
                        def detection_callback(df_filtrado, img_resultado, residue_list):
                            # Actualiza la UI cuando el hilo de detección termine
                            self.df_filtrado = df_filtrado
                            self.image_resultado = img_resultado
                            self.residue_list = residue_list
                            self.update_articles_table()  # Actualiza la tabla con los datos detectados
                            self.update_image(self.image_resultado)  # Actualiza la imagen en la UI

                        # Ejecuta el procesamiento en segundo plano
                                                # Definir el ROI usando las coordenadas disponibles en la clase
                        roi = (self.x1, self.y1, self.x2, self.y2)
                        self.processing_service.detected_objects_in_background(img_undistorted, 0.2, detection_callback,self.mmx,self.mmy,roi)
                        
                    except Exception as e:
                        print(f"Error al procesar la imagen: {e}")
                        self.root.after(500, self.iniciar_clasificacion)  # Asegurarse de que invoque el método correcto
                        return

                # Inicia la captura en segundo plano
                self.root.after(0, capture_image_in_background)

            # Verificamos la disponibilidad y procedemos a enviar los datos si está disponible
            self.verificar_disponibilidad()

            # Volver a ejecutar este ciclo después de 500 ms para no bloquear la interfaz
            self.root.after(500, self.iniciar_clasificacion)
        else:
            print("No puede iniciar sin conectarse al robot")


        
    def clasificacion(self):
        """
        Método principal de clasificación.
        """
        if not self.calibracion:
            print("No puede iniciar sin antes calibrar la camara")



        # Iniciar la clasificación de manera continua
        self.iniciar_clasificacion()  # Asegurarse de ejecutar el método correctamente

    def verificar_disponibilidad(self):
        def change_disponibilidad(command):
            if command == "OK":
                self.isDisponible = True

                self.enviar_datos_clasificados()
            else:
                self.isDisponible = False
                print("Dispositivo no disponible, esperando...")

        # Enviar el mensaje para verificar disponibilidad
        self.communication_service.send_and_receive("DISPONIBILIDAD", "BUFFER_VACIO", change_disponibilidad)

    def enviar_datos_clasificados(self):
        """
        Envía los datos clasificados al dispositivo si está disponible.
        """
        if self.isDisponible and self.df_filtrado is not None:

            def saveArticle(response):
                if response == "OK":
                    # Confirmar que las unidades son en milímetros
                    print("Enviando datos en milímetros:")
                    for x, y, z, _ in self.coordenadas_generator(self.df_filtrado):
                        print(f"x: {x} mm, y: {y} mm, z: {z} mm")
                    
                    resultJSON = self.generar_informacion(self.df_filtrado)
                    print("Resultado de clasificación:", resultJSON)
                    self.update_image(self.image_resultado)
                else:
                    print("Fallo la conexión:", response)

            def confirm_end(response):
                if response == "OK":
                    # Limpiar los datos
                    self.isDisponible = False
                    self.df_filtrado = None
                    self.image_resultado = None
                    self.residue_list = None
                else:
                    print("Fallo la confirmación de fin:", response)

            # Enviar los comandos de los objetos clasificados
            first_command = True
            c = self.offset

            for x, y, z, clase in self.coordenadas_generator(self.df_filtrado):
                command = f"{x},{y},{z},{c},{clase}"
                self.communication_service.send_and_receive(command, "OK", saveArticle)

                if first_command:
                    first_command = False
                    c = 0

            # Enviar mensaje de finalización
            self.communication_service.send_and_receive("FIN", "OK", confirm_end)


    def coordenadas_generator(self, df_filtrado, z=50):
        for _, row in df_filtrado.iterrows():
            # Convertir coordenadas de píxeles a milímetros
            x_mm, y_mm = self.transport_service.convert_pixels_to_mm(
                (row['xmin'] + row['xmax']) / 2,
                (row['ymin'] + row['ymax']) / 2,self.mmx,self.mmy
            )
            clase = int(row["class"])
            yield round(x_mm, 2), round(y_mm, 2), z, clase


    def tomar_foto(self):
        img = self.processing_service.capture_image()
        self.update_image(img)

    def calibrate_camera(self, square_size, physical_width_mm=200, physical_height_mm=200,x1=None,y1=None,x2=None,y2=None):
        """
        Calibra la cámara con parámetros personalizados.
        
        :param square_size: Tamaño del cuadrado en la imagen de calibración.
        :param physical_width_mm: Ancho físico en milímetros para la calibración del espacio.
        :param physical_height_mm: Altura física en milímetros para la calibración del espacio.
        """
        # Calibrar el espacio físico para asegurar que todo esté en milímetros
        print("Iniciando calibración por distorsión")
        self.mtx, self.dist = self.processing_service.calibrate(
            dirpath="./calibracion",
            prefix="tablero-ajedrez",
            image_format="jpg",
            square_size=square_size,
            width=7,
            height=7
        )
        
        print(f"Calibración por distorsión completada: mtx={self.mtx}, dist={self.dist}")

        print("Iniciando calibración del rectángulo")
        x1, x2, y1, y2 = self.transport_service.generate_square(x1, y1, x2, y2)  # Definiendo coordenadas del cuadrado
        print(f"Coordenadas del rectángulo generadas: x1={x1}, x2={x2}, y1={y1}, y2={y2}")

        pixels_per_mm_x, pixels_per_mm_y = self.transport_service.calibrate_to_physical_space(
            physical_width_mm=physical_width_mm,
            physical_height_mm=physical_height_mm
        )
        print(f"Calibración de espacio físico completada: pixels_per_mm_x={pixels_per_mm_x}, pixels_per_mm_y={pixels_per_mm_y}")
        
        print("Iniciando calibración del punto central")
        x_center, y_center = self.transport_service.calculate_center(x1, x2, y1, y2)
        print(f"Punto central calculado: x_center={x_center}, y_center={y_center}")

        # Seteamos el centro y el offset
        self.x_center = x_center
        self.y_center = y_center

        print("Iniciando calibración del offset")
        offset = self.transport_service.get_offset(x1, x2, pixels_per_mm_x)
        print(f"Offset calculado: offset={offset}")
        
        self.square_size = square_size 
        
        # Asignar valores a las propiedades del objeto
        self.calibracion = True
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.mmx = pixels_per_mm_x
        self.mmy = pixels_per_mm_y
        self.offset = offset
        
        print("Calibración terminada con éxito")


        

    def undistort_image(self, img):
        return self.processing_service.undistorted_image(img)

    def detectar_objetos(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        return self.processing_service.detected_objects(img_undistorted, confianza_minima, tamano_entrada)

    def generar_informacion(self, df_filtrado):
        return json.dumps(df_filtrado.to_dict(orient='records'))

    def update_image(self, img):
        img = Image.fromarray(img)  # Asegúrate de que 'img' sea un array de numpy
        ctk_img = ctk.CTkImage(img, size=(400, 300))  # Ajusta el tamaño de la imagen según sea necesario
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img  # Guardar una referencia para evitar que la imagen sea recolectada por el garbage collector

    def update_reports(self):
        for widget in self.reports_scrollable_frame.winfo_children():
            widget.destroy()

        headers = ["ID", "Nombre", "Categoría", "Confianza", "Fecha"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(self.reports_scrollable_frame, text=header, fg_color="#5e5e5e", text_color=self.btn_color)
            label.grid(row=0, column=col, padx=10, pady=5)

        reports = self.reports_service.get_all_rankings()
        for row_num, report in enumerate(reports, start=1):
            report_data = [report.id, report.nombre, report.categoria, report.confianza, report.fecha_deteccion]
            for col_num, data in enumerate(report_data):
                label = ctk.CTkLabel(self.reports_scrollable_frame, text=data, fg_color="#3e3e3e", text_color=self.btn_color)
                label.grid(row=row_num, column=col_num, padx=10, pady=5)

        self.update_statistics(reports)

    def filter_by_category(self):
        category = self.get_user_input("Ingrese la categoría a filtrar")
        reports = self.reports_service.filter_by_category(category)
        self.update_reports_list(reports)

    def filter_by_confidence(self):
        min_confidence = self.get_user_input("Ingrese la confianza mínima a filtrar")
        reports = self.reports_service.filter_by_confidence(float(min_confidence))
        self.update_reports_list(reports)

    def delete_selected(self):
        report_id = self.selected_report
        if report_id is not None:
            self.reports_service.delete_ranking(report_id)
            self.update_reports()
        else:
            messagebox.showerror("Error", "No se ha seleccionado ningún reporte.")

    def edit_selected(self):
        report_id = self.selected_report
        if report_id is not None:
            new_data = self.get_user_input("Ingrese los nuevos datos en formato JSON")
            report = self.reports_service.get_ranking_by_id(report_id)
            for key, value in json.loads(new_data).items():
                setattr(report, key, value)
            self.reports_service.residue_repository.update_residue(report_id, **report.__dict__)
            self.update_reports()
        else:
            messagebox.showerror("Error", "No se ha seleccionado ningún reporte.")

    def get_user_input(self, prompt):
        user_input = ctk.simpledialog.askstring("Input", prompt, parent=self)
        return user_input

    def update_reports_list(self, reports):
        for widget in self.reports_scrollable_frame.winfo_children():
            widget.destroy()

        headers = ["ID", "Nombre", "Categoría", "Confianza", "Fecha"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(self.reports_scrollable_frame, text=header, fg_color=self.img_frame_color, text_color=self.btn_color)
            label.grid(row=0, column=col, padx=10, pady=5)

        for row_num, report in enumerate(reports, start=1):
            report_data = [report.id, report.nombre, report.categoria, report.confianza, report.fecha_deteccion]
            for col_num, data in enumerate(report_data):
                label = ctk.CTkLabel(self.reports_scrollable_frame, text=data, fg_color=self.img_frame_color, text_color=self.btn_color)
                label.grid(row=row_num, column=col_num, padx=10, pady=5)

    # Método para actualizar la vista según la opción seleccionada
    def update_view(self, selected_option):
        reports = self.reports_service.get_all_rankings()  # Obtener los datos de informes

        if selected_option == "Lista de Clasificación":
            self.stats_panel.grid_remove()
            self.reports_scrollable_frame.grid()
            self.update_reports_list(reports)
        elif selected_option == "Gráfico de Torta":
            self.reports_scrollable_frame.grid_remove()
            self.daily_histogram.grid_remove()
            self.stats_panel.grid()
            self.category_pie_chart.grid()
            self.update_statistics(reports, chart_type="pie")
        elif selected_option == "Histograma":
            self.reports_scrollable_frame.grid_remove()
            self.category_pie_chart.grid_remove()
            self.stats_panel.grid()
            self.daily_histogram.grid()
            self.update_statistics(reports, chart_type="histogram")

    # Modificamos la función para que acepte el tipo de gráfico a mostrar
    def update_statistics(self, reports, chart_type="pie"):
        total_residues = len(reports)
        self.total_residues_label.configure(text=f"Total de Residuos: {total_residues}")

        categories = [report.categoria for report in reports]
        category_counts = {category: categories.count(category) for category in set(categories)}

        if chart_type == "pie":
            # Tamaño reducido de la figura
            fig1, ax1 = plt.subplots(figsize=(4, 3))  # Ajustar tamaño de gráfico (ancho, alto)
            ax1.pie(category_counts.values(), labels=category_counts.keys(), autopct='%1.1f%%')
            ax1.axis('equal')
            self.update_figure(self.category_pie_chart, fig1)
        elif chart_type == "histogram":
            dates = [report.fecha_deteccion for report in reports]
            date_counts = {date: dates.count(date) for date in set(dates)}
            
            # Tamaño reducido de la figura
            fig2, ax2 = plt.subplots(figsize=(4, 3))  # Ajustar tamaño de gráfico (ancho, alto)
            ax2.bar(date_counts.keys(), date_counts.values())
            ax2.set_xlabel('Fecha')
            ax2.set_ylabel('Cantidad de Residuos')
            self.update_figure(self.daily_histogram, fig2)

    def update_figure(self, container, figure):
        for widget in container.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='none', expand=True)


    def start_communication(self):
            # CALLBACK
            def handle_response(response):
                if response == "OK":
                    self.conected = True
                    print("Conexion establecida con exito")
                else:
                    print("Fallo la conexion", response)
            self.communication_service.send_and_receive("CONECTAR", "Conectado", handle_response)

