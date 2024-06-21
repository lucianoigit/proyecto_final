import customtkinter as ctk
from PIL import Image, ImageTk
import time
import json
import os
from app.abstracts.ICommunication import CommunicationInterface
from app.abstracts.IProcessing import ProcessingInterface
import sys

class View(ctk.CTk):
    def __init__(self, communication_service: CommunicationInterface, processing_service: ProcessingInterface):
        super().__init__()
        self.title("Delta Robot")
        self.geometry("800x600")
        self.communication_service = communication_service
        self.processing_service = processing_service
        self.mtx = None
        self.dist = None
        self.calibracion = False
        self.reports = []
        self.image = None

        self.communication_service.initialize_communication()
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Menú de navegación en la parte inferior
        menu_bar = ctk.CTkFrame(self, corner_radius=0, fg_color="#3e3e3e")
        menu_bar.grid(row=2, column=0, sticky="ew")
        
        connectivity_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/connectivity.png"), command=self.connectivity, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        connectivity_button.grid(row=0, column=0, padx=10, pady=10)
        
        start_section_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/start.png"), command=self.show_main_panel, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        start_section_button.grid(row=0, column=1, padx=10, pady=10)
        
        configure_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/settings.png"), command=self.show_configure_panel, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        configure_button.grid(row=0, column=2, padx=10, pady=10)
        
        dashboard_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/dashboard.png"), command=self.show_dashboard, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        dashboard_button.grid(row=0, column=3, padx=10, pady=10)
        
        close_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/close.png"), command=self.close_application, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        close_button.grid(row=0, column=4, padx=10, pady=10)

        self.panels = {}

        main_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        main_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.panels["main"] = main_panel

        main_panel.grid_columnconfigure((0, 3), weight=1)
        main_panel.grid_columnconfigure((1, 2), weight=0)
        main_panel.grid_rowconfigure(2, weight=1)  # Adjust row for image display

        start_button = ctk.CTkButton(main_panel, text="", image=self.load_icon("icons/iniciar.png"), command=self.start_process, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        start_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        stop_button = ctk.CTkButton(main_panel, text="", image=self.load_icon("icons/stop.png"), command=self.stop_process, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        stop_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.image_label = ctk.CTkLabel(main_panel, text="Imagen clasificada aparecerá aquí", anchor="center", fg_color="#3e3e3e", text_color="#ffffff")
        self.image_label.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")


        # Panel de informes
        reports_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        reports_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.panels["reports"] = reports_panel
        
        reports_panel.grid_columnconfigure(0, weight=1)
        reports_panel.grid_rowconfigure(0, weight=1)

        self.reports_text_box = ctk.CTkTextbox(reports_panel, state="disabled", fg_color="#5e5e5e", text_color="#ffffff")
        self.reports_text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Panel de configuración
        configure_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        configure_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.panels["configure"] = configure_panel

        configure_panel.grid_columnconfigure((0, 1), weight=1)
        configure_panel.grid_rowconfigure((0, 1), weight=1)

        calibration_button = ctk.CTkButton(configure_panel, text="Calibración de Cámara", command=self.calibrate_camera, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        calibration_button.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ml_model_button = ctk.CTkButton(configure_panel, text="Calibración de Modelo ML", command=self.calibrate_ml_model, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        ml_model_button.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        camera_type_button = ctk.CTkButton(configure_panel, text="Calibración Tipo de Cámara", command=self.calibrate_camera_type, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        camera_type_button.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        conveyor_config_button = ctk.CTkButton(configure_panel, text="Configuración de Cinta Transportadora", command=self.configure_conveyor, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        conveyor_config_button.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.show_main_panel()
        self.receive_data()

    def load_icon(self, path):
        # Obtener la ruta base correcta dependiendo de si el script está empaquetado por PyInstaller o no
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, path)
        try:
            # Cargar la imagen y ajustar el tamaño según sea necesario
            return ImageTk.PhotoImage(Image.open(icon_path).resize((50, 50)))
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

    def hide_all_panels(self):
        for panel in self.panels.values():
            panel.grid_remove()
    def receive_data(self):
        try:
            # Verificar si el servicio de comunicación está listo
            if self.communication_service and self.communication_service.ser and self.communication_service.ser.is_open:
                data = self.communication_service.receive_data()
                if data:
                    self.text_box.insert(ctk.END, f"{data}\n")
                    self.text_box.see(ctk.END)
        except Exception as e:
            print(f"Error al recibir datos: {e}")

        # Programar la siguiente llamada de receive_data
        self.after(100, self.receive_data)


    def send_message(self):
        message = self.message_entry.get() + '\n'
        self.communication_service.send_message(message)
        self.message_entry.delete(0, ctk.END)

    def connectivity(self):
        # Lógica para conectividad
        pass

    def start_process(self):
        self.clasificacion()

    def stop_process(self):
        pass


    def calibrate_camera(self):
        # Lógica para calibración de cámara
        pass

    def calibrate_ml_model(self):
        # Lógica para calibración de modelo ML
        pass

    def calibrate_camera_type(self):
        # Lógica para calibración de tipo de cámara
        pass

    def configure_conveyor(self):
        # Lógica para configuración de cinta transportadora
        pass

    def configure(self):
        self.show_configure_panel()

    def show_dashboard(self):
        self.show_reports_panel()

    def close_application(self):
        self.quit()

    def clasificacion(self):
        if not self.calibracion:
            self.mtx, self.dist = self.processing_service.calibrate(dirpath="./calibracion", prefix="tablero-ajedrez", image_format="jpg", square_size=30, width=7, height=7)
            self.calibracion = True

        max_retries = 3  # Máximo número de reintentos
        attempts = 0

        while attempts < max_retries:
            self.communication_service.send_message("¿Estás listo?\n")
            img = self.processing_service.capture_image()
            img_undistorted = self.processing_service.undistorted_image(img)
            df_filtrado, imagenresutado = self.processing_service.detected_objects(img_undistorted)
            start_time = time.time()

            while time.time() - start_time < 5:  # Espera 5 segundos
                data = self.communication_service.receive_data()
                if data == "OK":
                    resultJSON = self.generar_informacion(df_filtrado)
                    print("Resultado de clasificación:", resultJSON)
                    self.update_image(imagenresutado)
                    self.reports.append(resultJSON)
                    return

            print("No se recibió respuesta 'OK' después de 5 segundos. Reintentando...")
            attempts += 1

        print("No se recibió respuesta 'OK' después de varios intentos. Abortando la operación.")
        sys.exit(1)  # Salir del programa con un código de error

    def tomar_foto(self):
        img = self.processing_service.capture_image()
        self.update_image(img)

    def calibrate(self):
        self.mtx, self.dist = self.processing_service.calibrate(dirpath="./calibracion", prefix="tablero-ajedrez", image_format="jpg", square_size=30, width=7, height=7)
        self.calibracion = True

    def undistort_image(self, img):
        return self.processing_service.undistorted_image(img)

    def detectar_objetos(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        return self.processing_service.detected_objects(img_undistorted, confianza_minima, tamano_entrada)

    def generar_informacion(self, df_filtrado):
        return json.dumps(df_filtrado.to_dict(orient='records'))

    def update_image(self, img):
        # Convertir la imagen a un formato que pueda ser usado por Tkinter
        img = Image.fromarray(img)  # Asegúrate de que 'img' sea un array de numpy
        ctk_img = ctk.CTkImage(img, size=(400, 300))  # Ajusta el tamaño de la imagen según sea necesario
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img  # Guardar una referencia para evitar que la imagen sea recolectada por el garbage collector

    def update_reports(self):
        self.reports_text_box.configure(state="normal")
        self.reports_text_box.delete("1.0", ctk.END)
        for report in self.reports:
            self.reports_text_box.insert(ctk.END, report + "\n")
        self.reports_text_box.configure(state="disabled")
