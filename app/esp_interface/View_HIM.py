import customtkinter as ctk
from PIL import Image, ImageTk,ImageOps, ImageDraw
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
import threading
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
        self.calibration_model = False
        self.reports = []
        self.image = None
        self.conected = False
        self.x_center =None
        self.y_center = None
        self.offset = None
        self.isOpen = False
        self.isDisponible = False
        self.image_resultado =  None
        self.df_filtrado = None
        self.image_resultado = None
        self.residue_list = None
        self.x1=None
        self.x2=None
        self.x3 = None
        self.x4 = None
        self.y1=None
        self.y2=None
        self.y3=None
        self.y4= None
        self.mmx = 0.0000
        self.mmy = 0.0000 
        self.square_size = 50 
        self.points = []
        self.isProcessing = False
        self.first_run = True
        self.roi = None
        self.max_speed = None
        self.moving_conveyor_belt_speed=None
        self.moving_home_max_speed=None
        self.categories = []
        self.stopProcess = False
        self.led = False

        

        # Paleta de colores aplicada
        self.bg_color = "#dbe7fc"  # Fondo principal
        self.btn_color = "#bcbefa"  # Color de los botones
        self.nav_color = "#ffffff"  # Fondo del menú de navegación
        self.img_frame_color = "#ffffff"  # Fondo del cuadro de imagen
        self.text_color = "#000000"  # Color del texto
        self.verde = "#4CAF50"  # Verde claro, equilibrado y agradable
        self.rojo = "#FF6347"  # Rojo tomate, un tono cálido y suave



        # Aplicar fondo principal
        self.configure(fg_color=self.bg_color)

        self.panels = {}
        self.create_widgets()
        self.i = 0
        
        self.img = None
        self.update_flag = False

        threading.Thread(target=self.frame_real_time, daemon=True).start()
        self.update_gui()

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
                                            image=self.load_icon("icons/home.png"),
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
        

        main_panel.grid_columnconfigure(1, weight=1)

        # Crear botón de inicio y detener
        self.start_button = ctk.CTkButton(main_panel, text="", 
                                        command=self.on_start_button_clicked, 
                                        image=self.load_icon("icons/start.png"),
                                        fg_color=self.img_frame_color, 
                                        border_color=self.btn_color,              
                                        border_width=2,
                                        hover_color=self.bg_color,
                                        text_color=self.text_color)
        self.start_button.configure(state="disabled")
        self.start_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew") 

        self.stop_button = ctk.CTkButton(main_panel, text="", 
                                        command=self.on_stop_button_clicked, 
                                        image=self.load_icon("icons/stop.png"),
                                        fg_color=self.img_frame_color, 
                                        border_width=2,
                                        border_color=self.btn_color,
                                        hover_color=self.bg_color,
                                        text_color=self.text_color)

        self.stop_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.stop_button.grid_remove()  # Inicialmente ocultamos el botón de detener



        # Área de imagen clasificada
        self.image_label = ctk.CTkLabel(main_panel, text="", anchor="center",
                                        fg_color=self.img_frame_color, text_color=self.text_color)
        # self.image_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.image_label.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        self.image_label2 = ctk.CTkLabel(main_panel, text="", anchor="center",
                                  fg_color=self.img_frame_color, text_color=self.text_color)
        self.image_label2.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")


        # Tabla para mostrar los últimos 5 artículos clasificados
        self.articles_frame = ctk.CTkScrollableFrame(main_panel, fg_color=self.img_frame_color)
        """   self.articles_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew") """


        # Configurar las columnas de la tabla
        # Crear la tabla con formato estilo Excel
        """  headers = ["ID", "Nombre", "Categoría", "Confianza", "Fecha"]
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
        self.update_articles_table()  """

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
            width=640,  # Ancho ajustado
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

        self.class_hitogram = ctk.CTkLabel(self.stats_panel, text="", fg_color=self.btn_color, text_color=self.btn_color)
        self.class_hitogram.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

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
        self.ml_model_button = ctk.CTkButton(configure_panel, text="Calibración de Modelo ML", 
                                        command=self.configure_classifier, fg_color=self.nav_color, 
                                        hover_color="#a3a7d9", text_color=self.text_color)
        self.ml_model_button.configure(state="disabled")
        self.ml_model_button.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    


        # Botón de configuración de cinta transportadora
        """         conveyor_config_button = ctk.CTkButton(configure_panel, text="Configuración de velocidad", 
                                            command=self.configure_conveyor, fg_color=self.btn_color, 
                                            hover_color="#a3a7d9", text_color=self.text_color)
        conveyor_config_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew") """

        # Ajustar las proporciones de las columnas y filas del grid
        for i in range(2):  # Ajustar el número según la cantidad de filas o columnas que necesites
            configure_panel.grid_columnconfigure(i, weight=1)
            configure_panel.grid_rowconfigure(i, weight=1)

        self.show_main_panel()
        #self.receive_data()
        
        

    def configure_classifier(self):
        # Crear ventana de configuración    # Crear ventana de configuración
        classifier_window = ctk.CTkToplevel(self)
        classifier_window.title("Configuración de Clasificador")
        classifier_window.geometry("640x480")

        # # Botón para actualizar interfaz
        # refresh_button = ctk.CTkButton(classifier_window, text="Actualizar Interfaz", command=self.update_category_frame)
        # refresh_button.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        # Frame para mostrar y configurar categorías
        self.category_frame = ctk.CTkFrame(classifier_window)
        self.category_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Actualizar la interfaz inicialmente
        self.update_category_frame()

    def update_category_frame(self):
        """Actualizar el frame con las categorías almacenadas."""
        # Limpiar el frame antes de mostrar las categorías
        for widget in self.category_frame.winfo_children():
            widget.destroy()

        if not self.categories:
            # No hay categorías, mostrar campos para agregar nuevas
            label = ctk.CTkLabel(self.category_frame, text="No hay categorías almacenadas. Agregue una nueva.")
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            self.create_new_category_fields()
        else:
            # Mostrar categorías existentes con opción de eliminar
            for i, category in enumerate(self.categories):
                name, x, y, z = category
                label = ctk.CTkLabel(self.category_frame, text=f"{name} (X={x}, Y={y}, Z={z})")
                label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

                delete_button = ctk.CTkButton(
                    self.category_frame, 
                    text="Eliminar",
                    command=lambda n=name: self.delete_category(n)
                )
                delete_button.grid(row=i, column=1, padx=5, pady=5)

            # Agregar campos para nuevas categorías al final
            self.create_new_category_fields(start_row=len(self.categories))

    def create_new_category_fields(self, start_row=0):
        """Crear campos para agregar nuevas categorías con posiciones predefinidas."""
        positions = [(-80, 80), (80, 80), (-80, -80), (80, -80)]

        for i, pos in enumerate(positions):
            label = ctk.CTkLabel(self.category_frame, text=f"Categoría (X={pos[0]}, Y={pos[1]})")
            label.grid(row=start_row + i, column=0, padx=10, pady=5, sticky="w")

            name_entry = ctk.CTkEntry(self.category_frame, placeholder_text="Nombre de Categoría")
            name_entry.grid(row=start_row + i, column=1, padx=5, pady=5)

            save_button = ctk.CTkButton(
                self.category_frame, 
                text="Guardar",
                command=lambda e=name_entry, x=pos[0], y=pos[1]: self.add_category(e, x, y)
            )
            save_button.grid(row=start_row + i, column=2, padx=5, pady=5)

    def add_category(self, name_entry, x, y):
        """Agregar una nueva categoría al sistema con posición fija."""
        name = name_entry.get()
        z = -500  # Posición Z fija

        if not name:
            print("El nombre de la categoría es obligatorio.")
            return

        command = f"ADD_CATEGORY {name},{x},{y},{z}"

        def callback(response):
            if response == "OK":
                print(f"Categoría '{name}' añadida con éxito en posición ({x}, {y}, {z}).")
                self.categories.append((name, x, y, z))  # Guardar en memoria
                self.update_category_frame()
                self.calibration_model = True
                self.start_button.configure(state="normal")
            else:
                print(f"Error al añadir la categoría '{name}'. Respuesta: {response}")

        self.communication_service.send_and_receive(command, f"Categoría añadida", callback)

    def delete_category(self, name):
        """Eliminar una categoría del sistema y de la memoria."""
        command = f"REMOVE_CATEGORY {name}"
        
        upperName= name.upper()

        def callback(response):
            if response == "OK":
                print(f"Categoría '{name}' eliminada con éxito.")
                self.categories = [c for c in self.categories if c[0] != name]  # Eliminar de memoria
                self.update_category_frame()
            else:
                print(f"Error al eliminar la categoría '{name}'. Respuesta: {response}")

        self.communication_service.send_and_receive(command, f"Categoría eliminada: {upperName}", callback)

    def configure_conveyor(self):
        # Crear ventana modal para configuración de velocidad
        conveyor_window = ctk.CTkToplevel(self)
        conveyor_window.title("Configuración de Velocidad")
        conveyor_window.geometry("640x480")

        # Variables a configurar
        self.speed_vars = {
            "Speed": None,
            "MaxSpeed": None,
            "MovingHomeSpeed": None,
            "MovingHomeMaxSpeed": None,
            "MovingHomeAcceleration": None,
            "MovingConveyorBeltSpeed": None,
            "MovingConveyorBeltMaxSpeed": None,
            "MovingConveyorBeltAcceleration": None
        }

        # Crear campos de entrada y botones para cada variable de velocidad
        for i, var in enumerate(self.speed_vars):
            label = ctk.CTkLabel(conveyor_window, text=var)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")

            entry = ctk.CTkEntry(conveyor_window)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.speed_vars[var] = entry

            button = ctk.CTkButton(conveyor_window, text="Guardar",
                                   command=lambda v=var, e=entry: self.set_speed(v, e))
            button.grid(row=i, column=2, padx=10, pady=5)

            # Cargar valor actual
            self.communication_service.get_data(f"GET {var}", lambda response, var=var: self.update_field(response, var))

    def update_field(self, response, variable):
        # Actualiza campo de entrada con valor recibido
        try:
            value = response.split(" ")[1]
            if variable in self.speed_vars:
                self.speed_vars[variable].delete(0, ctk.END)
                self.speed_vars[variable].insert(0, value)
                print(f"{variable} cargado con valor {value}")
        except IndexError:
            print(f"Error al procesar la respuesta para {variable}: {response}")

    def set_speed(self, variable, entry):
        # Envía el valor ingresado para la variable de velocidad
        value = entry.get()
        command = f"SET {variable} {value}"

        def callback(response):
            if response == "OK":
                print(f"{variable} configurado exitosamente a {value}")
            else:
                print(f"Error al configurar {variable}. Respuesta recibida: {response}")

        self.communication_service.send_and_receive(command, f"{variable} {value}", callback)

        
    def ble(self):
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
        while self.isProcessing == True:
            continue
        self.reset_procesamiento()
        self.stop_process()
        self.first_run = True

        # Ocultar el botón de detener y mostrar el de inicio nuevamente
        self.stop_button.grid_remove()
        self.start_button.grid()

    def calibrate_camera_type(self):
        calibration_window = ctk.CTkToplevel(self)
        calibration_window.title("Configuración de Calibración")
        calibration_window.geometry("400x300")

        calibration_window.grid_columnconfigure(0, weight=1)
        calibration_window.grid_rowconfigure(1, weight=1)

        fram = ctk.CTkFrame(calibration_window, width=380, height=280)
        fram.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        fram.grid_columnconfigure(0, weight=1)
        # fram.pack(fill="both", expand=True, padx=10, pady=10)

        # Instruction label
        instruction_label = ctk.CTkLabel(fram, text="Por favor, seleccione los puntos en la imagen", 
                                            wraplength=360, justify="center")
        instruction_label.grid(row=0, column=0, padx=10, pady=(10, 20), sticky="ew")

        # Calibration status label (initially empty)
        self.calibration_status_label = ctk.CTkLabel(fram, text="", 
                                                        font=("Arial", 16, "bold"),
                                                        text_color="green")
        self.calibration_status_label.grid(row=2, column=0, padx=10, pady=(0, 20), sticky="ew")

        self.points = []
        # instruction_label = ctk.CTkLabel(fram, text=("Por favor, seleccione los puntos en la imagen"))
        # instruction_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 20), sticky="ew")

        

        # # Etiqueta para mostrar el estado de la calibración
        # self.calibration_status_label = ctk.CTkLabel(fram, text="", font=("Arial",16,"bold"))
        # self.calibration_status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="ew")
        
        # self.points = []

        def open_camera_and_select_points():
            self.calibration_status_label.configure(text="")  # Reset status label
            self.points.clear()
            cv2.namedWindow("Seleccione cuatro puntos",cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Seleccione cuatro puntos",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
            cv2.setMouseCallback("Seleccione cuatro puntos", click_event)

            self.start_button.configure(state="normal")

            while True:
                frame = self.picam2.capture_array()
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Dibujar puntos seleccionados
                for point in self.points:
                    cv2.circle(frame_bgr, point, 5, (255, 0, 0), -1)

                # Dibujar segmentos entre puntos seleccionados
                if len(self.points) > 1:
                    for i in range(len(self.points) - 1):
                        cv2.line(frame_bgr, self.points[i], self.points[i+1], (0, 255, 0), 2)
                

                if len(self.points) == 4:

                    ordered_points = ordenar_puntos(self.points)
                    # (x1, y1), (x2, y2), (x3, y3), (x4, y4) = self.points   
                    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = ordered_points

                    cv2.polylines(frame_bgr, [np.array(ordered_points)], isClosed=True, color=(0, 255, 0), thickness=2)
                    
                    self.calibrate_camera(square_size=400, physical_width_mm=200, physical_height_mm=200,
                                      x1=x1, y1=y1, 
                                      x2=x2, y2=y2, 
                                      x3=x3, y3=y3,
                                      x4=x4, y4=y4)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame_bgr, "Guardando...", (50, 450), font, 1, (0, 255, 255), 2, cv2.LINE_AA)
                    cv2.imshow("Seleccione cuatro puntos", frame_bgr)
                    
                    cv2.waitKey(2000)
                    
                    # Actualizar la leyenda después de la calibración
                    self.calibration_status_label.configure(text="La calibración se realizó con éxito")
                    
                    # Hide the button after successful calibration
                    select_points_button.grid_remove()

                    calibration_window.update()  # Asegura que el texto se muestre inmediatamente

                    # Esperar dos segundos antes de cerrar la ventana
                    calibration_window.after(2000, calibration_window.destroy)
                    
                    break
                else:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(frame_bgr, 'Seleccione 4 puntos', (50, 450), font, 1, (0, 255, 255), 2, cv2.LINE_AA)

                cv2.imshow("Seleccione cuatro puntos", frame_bgr)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cv2.destroyAllWindows()
        select_points_button = ctk.CTkButton(fram, text="Seleccionar Puntos en la Cámara", command=open_camera_and_select_points)
        select_points_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        # select_points_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.points.append((x, y))
                print(f"Punto seleccionado: {x, y}")

        def ordenar_puntos(puntos):
            centroid = (sum([p[0] for p in puntos]) / len(puntos), sum([p[1] for p in puntos]))
            return sorted(puntos, key=lambda p: np.arctan2(p[1] - centroid[1], p[0] - centroid[0]))

        # labels = [
        #     "Tamaño del cuadrado:", "Ancho físico (mm):", "Altura física (mm):", 
        #     "Coordenada X1:", "Coordenada Y1:", "Coordenada X2:", "Coordenada Y2:", 
        #     "Coordenada X3:", "Coordenada Y3:", "Coordenada X4:", "Coordenada Y4:"
        # ]
        # entries = []
        # for i, label_text in enumerate(labels):
        #     label = ctk.CTkLabel(scrollable_frame, text=label_text)
        #     label.grid(row=i + 1, column=0, padx=5, pady=5, sticky="w")
        #     entry = ctk.CTkEntry(scrollable_frame)
        #     entry.grid(row=i + 1, column=1, padx=5, pady=5, sticky="ew")
        #     entries.append(entry)

        # (square_size_entry, width_entry, height_entry, x1_entry, y1_entry, x2_entry, y2_entry, 
        # x3_entry, y3_entry, x4_entry, y4_entry) = entries

        
        # select_points_button.grid(row=len(labels) + 1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # start_button.grid(row=len(labels) + 2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # scrollable_frame.grid_columnconfigure(1, weight=1)


        
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
        # if self.calibration_model and self.calibracion:
            
        self.ml_model_button.configure(state="normal")

        self.communication_service.initialize_communication()
        if self.led == False:
            self.communication_service.send_message("LED_ON")
        else:
            self.communication_service.send_message("LED_OFF")

        isOpen = self.communication_service.getStatus()
        
        print ("serial status", isOpen)
        
        self.isOpen =  isOpen
        self.led = not self.led

  
 

 

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
        self.stopProcess = False
        self.clasificacion()

    def stop_process(self):
        self.stopProcess = True
        



    def calibrate_ml_model(self):
        # Lógica para calibración de modelo ML
        pass



    def show_dashboard(self):
        self.show_reports_panel()

    def close_application(self):
        
        def callback(response):
            if(response =="OK"):
                self.quit()  
        
        
        self.communication_service.send_and_receive("NOHOME 0.0,0.0,-700.0,0.0","OK",callback)
        
        
    def iniciar_clasificacion(self):
        if self.isOpen is True and self.stopProcess is False:

            if not self.isProcessing:
                # print("### Iniciando proceso de clasificación ###")
                # print("relacion x ", self.mmx)
                # print("relacion y ", self.mmy)
                self.isProcessing = True
                if self.df_filtrado is None or self.df_filtrado.empty:
                    print("Entramos a la clasificación - Primer ciclo o nuevo inicio.")

                    #def capture_image_in_background():
                    print("Capturando imagen en segundo plano...")
                    img = self.processing_service.capture_image()
                    
                
                    if img is None:
                        print("Error: No se pudo capturar la imagen. Reiniciando proceso.")
                        self.root.after(500, self.reset_procesamiento)
                        return

                    try:
                        img_undistorted = img
                        
                        print("Imagen capturada y corregida para distorsión.")

                        def detection_callback(df_filtrado, img_resultado, residue_list):
                            self.df_filtrado = df_filtrado
                            self.image_resultado = img_resultado
                            self.residue_list = residue_list
                            print("Clasificación completada, resultados almacenados en memoria.")
                            #self.update_articles_table()
                            self.update_image(self.image_resultado)
                            self.isProcessing = False


                            if self.first_run:
                                print("Primer ciclo de clasificación: enviando datos sin esperar START.")
                                self.first_run = False
                                self.verificar_disponibilidad()
                            else:
                                print("Ciclo posterior a primer ciclo: esperando disponibilidad.")
                                self.esperar_start()

                        # Suponiendo que self.points contiene los cuatro puntos seleccionados
                        

                        # Pasar el ROI calculado al procesamiento de detección de objetos
                        self.processing_service.detected_objects_in_background(
                            img_undistorted, 0.8, detection_callback, self.mmx, self.mmy, self.roi,self.x_center,self.y_center,self.points
                        )

                    except Exception as e:
                        print(f"Error al procesar la imagen: {e}")
                        self.root.after(500, self.reset_procesamiento)

                    #self.root.after(10, capture_image_in_background)
                else:
                    print("Buffer de datos lleno. Verificando disponibilidad para enviar...")

            else:
                print("Ya se está clasificando, esperando a que el proceso actual termine.")
        else:
            print("Puerto serial desconectado.")

    def calculate_roi_from_points(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Calcula el rectángulo mínimo que contiene los cuatro puntos seleccionados.
        :param x1, y1: Coordenadas del primer punto.
        :param x2, y2: Coordenadas del segundo punto.
        :param x3, y3: Coordenadas del tercer punto.
        :param x4, y4: Coordenadas del cuarto punto.
        :return: Tupla que define el ROI en formato (x_min, y_min, x_max, y_max).
        """
        # Determinar los valores mínimos y máximos de x e y
        x_values = [x1, x2, x3, x4]
        y_values = [y1, y2, y3, y4]
        x_min, x_max = min(x_values), max(x_values)
        y_min, y_max = min(y_values), max(y_values)
        return (x_min, y_min, x_max, y_max)
    


    def enviar_datos_clasificados(self):
        if self.isDisponible and self.df_filtrado is not None:
            print("Iniciando envío de datos clasificados.")

            def saveArticle(response):
                if response == "OK":
                    print("Artículo enviado exitosamente.")
                else:
                    print("Error en el envío del artículo:", response)

            def noDetection(response):
                if response == "OK":
                    print("No se detectó ningún artículo.")
                else:
                    print("Error en movimiento de cinta:", response)

            def confirm_end(response):
                if response == "OK":
                    print("Confirmación de SEGUI recibida. Preparando para nuevo ciclo de clasificación.")
                    self.reset_procesamiento()  # Restablece para iniciar una nueva clasificación
                    self.iniciar_clasificacion()  # Captura nueva imagen y clasifica
                else:
                    print("Error en confirmación de fin:", response)

            if len(self.df_filtrado) == 0:
                command = f"{0.00},{0.00},{0.00},-200,nada"
                print(f"Enviando comando de único dato: {command}")
                self.communication_service.send_and_receive(command, "OK", noDetection)

            if len(self.df_filtrado) == 1:
                # Procesar y enviar el único elemento
                row = self.df_filtrado.iloc[0]
                x, y, z, clase = self.coordenada_unica(row)
                # Formatear x, y, z, c con 2 decimales
                command = f"{x:.2f},{y:.2f},{z:.2f},{self.offset:.2f},{clase}"
                print(f"Enviando comando de único dato: {command}")
                self.communication_service.send_and_receive(command, "OK", saveArticle)

            if len(self.df_filtrado) > 1:
                # Procesar y enviar múltiples elementos
                first_command = True
                c = self.offset

                for x, y, z, clase in self.coordenadas_generator(self.df_filtrado):
                    # Formatear x, y, z, c con 2 decimales
                    command = f"{x:.2f},{y:.2f},{z:.2f},{c:.2f},{clase}"
                    print(f"Enviando comando de datos: {command}")
                    self.communication_service.send_and_receive(command, "OK", saveArticle)

                    if first_command:
                        first_command = False
                        c = 0

            print("Enviando mensaje de finalización (FIN).")
            self.communication_service.send_and_receive("FIN", "SEGUI", confirm_end)


    def esperar_start(self):
        """
        Espera el mensaje 'START' para iniciar el envío de datos almacenados en memoria en los ciclos posteriores.
        """
        
        def on_start_received(response):
            if response == "START":
                print("Mensaje START recibido. Comenzando envío de datos clasificados desde memoria.")
                self.verificar_disponibilidad()
                
            else:
                print("Esperando mensaje START...")
                self.root.after(1000, self.esperar_start)

        print("Esperando mensaje START para comenzar el envío.")
        self.communication_service.receiver_and_action("START", on_start_received)

    def verificar_disponibilidad(self):
        def change_disponibilidad(command):
            if command == "OK":
                self.isDisponible = True
                print("Dispositivo disponible para enviar datos.")
                self.enviar_datos_clasificados()
            else:
                self.isDisponible = False
                print("Dispositivo no disponible, esperando para reintentar.")

            if not self.isDisponible:
                print("Reintentando verificación de disponibilidad en 1 segundo.")
                self.root.after(1000, self.verificar_disponibilidad)

        print("Enviando mensaje de disponibilidad.")
        self.communication_service.send_and_receive("DISPONIBILIDAD", "BUFFER_VACIO", change_disponibilidad)

    def reset_procesamiento(self):
        print("Reiniciando procesamiento. Limpiando datos de clasificación.")
        self.isProcessing = False
        self.df_filtrado = None
        self.image_resultado = None
        self.residue_list = None
        
    def coordenada_unica(self, row, z=-600):
        """
        Genera la coordenada para un único dato clasificado.
        """
        x_mm, y_mm = self.transport_service.convert_pixels_to_mm(
            (row["center_x"]) - self.x_center,
            (row["center_y"]) - self.y_center, self.mmx, self.mmy
        )
        clase = row["class_name"]
        print(f"Coordenada única generada: x={x_mm}, y={y_mm}, z={z}, clase={clase}")
        return round(x_mm, 2), round(y_mm, 2), z, clase
    
    def coordenadas_generator(self, df_filtrado, z=-600):
        print("Generando coordenadas para datos clasificados.")
        for _, row in df_filtrado.iterrows():
            x_mm, y_mm = self.transport_service.convert_pixels_to_mm(
            (row["center_x"])  - self.x_center,
            (row["center_y"]) - self.y_center, self.mmx, self.mmy
        )
            clase = row["class_name"]
            print(f"Coordenada generada: x={x_mm}, y={y_mm}, z={z}, clase={clase}")
            yield round(x_mm, 2), round(y_mm, 2), z, clase

    def clasificacion(self):
        """
        Método principal de clasificación.
        """
        if self.stopProcess == False:
            if not self.calibracion or not self.calibration_model:
                print("No puede iniciar sin antes calibrar la camara")
            else:
                self.iniciar_clasificacion()  # Asegurarse de ejecutar el método correctamente
            # Iniciar la clasificación de manera continua
        else:
            print("Error, no se puede iniciar la clasificacion")
  
    def tomar_foto(self):
        img = self.processing_service.capture_image()
     
        
    def calibrate_camera(self, square_size=400, physical_width_mm=200, physical_height_mm=200, x1=None, y1=None, x2=None, y2=None, x3=None, y3=None, x4=None, y4=None):
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

        print("Configurando coordenadas de los cuatro puntos del área de calibración.")
        self.x1, self.y1, self.x2, self.y2, self.x3, self.y3, self.x4, self.y4 = x1, y1, x2, y2, x3, y3, x4, y4

        pixels_per_mm_x, pixels_per_mm_y = self.transport_service.calibrate_to_physical_space(
            physical_width_mm,
            physical_height_mm,self.x1,self.x2,self.y1,self.y4
        )
        self.calculate_scale_factor()
        print(f"Calibración de espacio físico completada: pixels_per_mm_x={pixels_per_mm_x}, pixels_per_mm_y={pixels_per_mm_y}")

        centroid = self.calculate_centroid(self.points)
        x_center, y_center = centroid
        print(f"Punto central calculado: x_center={x_center}, y_center={y_center}")

        self.x_center = x_center
        self.y_center = y_center

        self.offset=-200
        self.square_size = square_size 
        self.calibracion = True

        
        print("Calibración de ROI basada en los puntos seleccionados.")

        
        print("Calibración completada con éxito")
        
    def calculate_centroid(self,points):
        """Calcula el centroide de un conjunto de puntos (vértices del polígono)."""
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        centroid_x = int(np.mean(x_coords))
        centroid_y = int(np.mean(y_coords))
                
        return (centroid_x,centroid_y)
    
    def undistort_image(self, img):
        return self.processing_service.undistorted_image(img)

    def detectar_objetos(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        return self.processing_service.detected_objects(img_undistorted, confianza_minima, tamano_entrada,self.mmx,self.mmy)

    def generar_informacion(self, df_filtrado):
        return json.dumps(df_filtrado.to_dict(orient='records'))


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
            self.class_hitogram.grid_remove()
            self.stats_panel.grid()
            self.category_pie_chart.grid()
            self.update_statistics(reports, chart_type="pie")
        elif selected_option == "Histograma":
            self.reports_scrollable_frame.grid_remove()
            self.category_pie_chart.grid_remove()
            self.stats_panel.grid()
            self.class_hitogram.grid()
            self.update_statistics(reports, chart_type="histogram")

    # Modificamos la función para que acepte el tipo de gráfico a mostrar
    def update_statistics(self, reports, chart_type="pie"):
        total_residues = len(reports)
        self.total_residues_label.configure(text=f"Total de Residuos: {total_residues}")

        categories = [report.categoria for report in reports]
        names = [report.nombre for report in reports]
        category_counts = {category: categories.count(category) for category in set(categories)}
        name_counts = {name: names.count(name) for name in set(names)}

        if chart_type == "pie":
            # Tamaño reducido de la figura
            fig1, ax1 = plt.subplots(figsize=(5, 2))  # Ajustar tamaño de gráfico (ancho, alto)
            ax1.pie(category_counts.values(), labels=category_counts.keys(), autopct='%1.1f%%')
            ax1.axis('equal')
            self.update_figure(self.category_pie_chart, fig1)
        elif chart_type == "histogram":

            
            # Tamaño reducido de la figura
            fig2, ax2 = plt.subplots(figsize=(5, 2))  # Ajustar tamaño de gráfico (ancho, alto)
            ax2.bar(name_counts.keys(), name_counts.values())
            ax2.set_xlabel('Clase')
            ax2.set_ylabel('Cantidad de Residuos')
            self.update_figure(self.class_hitogram, fig2)
                
    def update_image(self, img, roi=None):
        """
        Actualiza la etiqueta de la interfaz para mostrar la imagen procesada, incluyendo el ROI.
        """
        try:
            # img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

            # # Dibujar el ROI en la imagen si está definido

            # ctk_img = ctk.CTkImage(img_pil, size=(640, 480))
            # self.image_label.configure(image=ctk_img)
            # self.image_label.image = ctk_img


            imagen = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            imagen = imagen.resize((320, 240), Image.LANCZOS)
            imagen = ImageTk.PhotoImage(imagen)
            self.image_label.configure(image=imagen)
            self.image_label.image = imagen
        except Exception as e:
            print(f"Error al actualizar la imagen: {e}")
    
    def update_image_real_time(self):
        """
        Actualiza la etiqueta de la interfaz para mostrar la imagen original.
        """
        try:
            if self.img is not None:
                # Convierte la imagen de OpenCV (array de NumPy) a una imagen PIL
                imagen = Image.fromarray(self.img)
                imagen = imagen.resize((320, 240), Image.LANCZOS)
                
                # Convierte la imagen PIL directamente a un formato que CustomTkinter pueda manejar
                ctk_image = ctk.CTkImage(light_image=imagen, size=(320, 240))
                
                # Actualiza la etiqueta con la nueva imagen
                self.image_label2.configure(image=ctk_image)
                self.image_label2.image = ctk_image  # Mantener una referencia a la imagen
        except Exception as e:
            print(f"Error al actualizar la imagen en tiempo real: {e}")

    def frame_real_time(self):
        while True:  # Bucle infinito para capturar imágenes continuamente
            start_time = time.time()
            img = self.picam2.capture_array("main")  # Captura la imagen

            # Guardamos la imagen y establecemos el flag de actualización
            self.img = img
            self.update_flag = True

            # Controlamos la frecuencia de actualización (por ejemplo, 20 FPS)
            elapsed_time = time.time() - start_time
            time_to_sleep = max(0, (1/20) - elapsed_time)  # Controla a 20 FPS
            time.sleep(time_to_sleep)

    def update_gui(self):
        """
        Actualiza la interfaz en el hilo principal.
        """
        if self.update_flag:
            # Si hay una nueva imagen disponible, actualizamos la interfaz
            self.update_image_real_time()

            # Reseteamos el flag de actualización
            self.update_flag = False
        
        # Llamamos nuevamente a `update_gui()` para seguir actualizando la interfaz
        self.root.after(50, self.update_gui)  # Llamar cada 50 ms (20 FPS)


    def start_communication(self):
            # CALLBACK
            def handle_response(response):
                if response == "OK":
                    self.conected = True
                    print("Conexion establecida con exito")
                else:
                    print("Fallo la conexion", response)
            self.communication_service.send_and_receive("CONECTAR", "Conectado", handle_response)


    
    def calculate_scale_factor(self, reference_size=(200,200)):
        """
        Calcular el factor de escala para convertir pixeles a milímetros.
        
        :param reference_size: Tamaño de referencia en mm (ancho, alto)
        """
        def point_distance(p1, p2):
            return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

        distance_px = [
            point_distance(self.points[0], self.points[1]),
            point_distance(self.points[1], self.points[2]),
            point_distance(self.points[2], self.points[3]),
            point_distance(self.points[3], self.points[0])
        ]

        # Mapeo de distancias de referencia
        ref_width, ref_height = reference_size
        expected_side_lengths = [ref_width, ref_height, ref_width, ref_height]

        scale_factors = [expected / mesure for expected, mesure in zip(expected_side_lengths, distance_px)]
        self.mmy = np.mean(scale_factors)
        self.mmx = self.mmy

        print(f"Factor de escala (píxeles a mm): {self.mmy}")
        
    def update_figure(self, container, figure):
        for widget in container.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(figure, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)