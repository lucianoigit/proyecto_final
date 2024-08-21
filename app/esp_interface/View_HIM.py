import customtkinter as ctk
from PIL import Image, ImageTk
import time
import json
import os

from matplotlib import pyplot as plt
from app.abstracts.ICommunication import CommunicationInterface
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from app.abstracts.IProcessing import ProcessingInterface
import sys

from app.services.reports_service import ReportsService

class View(ctk.CTk):
    def __init__(self, communication_service: CommunicationInterface, processing_service: ProcessingInterface, reports_service: ReportsService):
        super().__init__()
        self.title("Delta Robot")
        self.geometry("800x480")
        #self.resizable(False,False)
        self.communication_service = communication_service
        self.processing_service = processing_service
        self.reports_service = reports_service
        self.mtx = None
        self.dist = None
        self.calibracion = False
        self.reports = []
        self.image = None

        self.panels = {}
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Menú de navegación en la parte inferior
        menu_bar = ctk.CTkFrame(self, corner_radius=0, fg_color="#3e3e3e")
        menu_bar.grid(row=2, column=0, sticky="ew")
        
        connectivity_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/connectivity.png"), command=self.show_connectivity_panel, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        connectivity_button.grid(row=0, column=0, padx=10, pady=10)

        connect = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/connectivity.png"), command=self.start_communication, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        connect.grid(row=2, column=0, padx=10, pady=10)
        
        start_section_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/start.png"), command=self.show_main_panel, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        start_section_button.grid(row=0, column=1, padx=10, pady=10)
        
        configure_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/settings.png"), command=self.show_configure_panel, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        configure_button.grid(row=0, column=2, padx=10, pady=10)
        
        dashboard_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/dashboard.png"), command=self.show_dashboard, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        dashboard_button.grid(row=0, column=3, padx=10, pady=10)
        
        close_button = ctk.CTkButton(menu_bar, text="", image=self.load_icon("icons/close.png"), command=self.close_application, width=80, height=80, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        close_button.grid(row=0, column=4, padx=10, pady=10)

        # Panel principal
        main_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        main_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.panels["main"] = main_panel

        main_panel.grid_columnconfigure((0, 3), weight=1)
        main_panel.grid_columnconfigure((1, 2), weight=0)
        main_panel.grid_rowconfigure(2, weight=1)

        start_button = ctk.CTkButton(main_panel, text="", image=self.load_icon("icons/iniciar.png"), command=self.start_process, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        start_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        stop_button = ctk.CTkButton(main_panel, text="", image=self.load_icon("icons/stop.png"), command=self.stop_process, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        stop_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.image_label = ctk.CTkLabel(main_panel, text="Imagen clasificada aparecerá aquí", anchor="center", fg_color="#3e3e3e", text_color="#ffffff")
        self.image_label.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

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

        # Panel de informes
        reports_panel = ctk.CTkFrame(self, fg_color="#3e3e3e")
        reports_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.panels["reports"] = reports_panel
        
        reports_panel.grid_columnconfigure(1, weight=1)
        reports_panel.grid_rowconfigure(1, weight=1)

        self.reports_scrollable_frame = ctk.CTkScrollableFrame(reports_panel, fg_color="#3e3e3e")
        self.reports_scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        filter_category_button = ctk.CTkButton(reports_panel, text="Filtrar por Categoría", command=self.filter_by_category, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        filter_category_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        filter_confidence_button = ctk.CTkButton(reports_panel, text="Filtrar por Confianza", command=self.filter_by_confidence, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        filter_confidence_button.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        delete_button = ctk.CTkButton(reports_panel, text="Eliminar Seleccionado", command=self.delete_selected, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        delete_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        edit_button = ctk.CTkButton(reports_panel, text="Editar Seleccionado", command=self.edit_selected, fg_color="#5e5e5e", hover_color="#7e7e7e", text_color="#ffffff")
        edit_button.grid(row=1, column=3, padx=10, pady=10, sticky="ew")

        # Paneles de estadísticas
        stats_panel = ctk.CTkFrame(reports_panel, fg_color="#3e3e3e")
        stats_panel.grid(row=0, column=2, sticky="nsew", padx=20, pady=20)
        
        self.total_residues_label = ctk.CTkLabel(stats_panel, text="", fg_color="#5e5e5e", text_color="#ffffff")
        self.total_residues_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.category_pie_chart = ctk.CTkLabel(stats_panel, text="", text_color="#ffffff")
        self.category_pie_chart.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.daily_histogram = ctk.CTkLabel(stats_panel, text="", fg_color="#5e5e5e", text_color="#ffffff")
        self.daily_histogram.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

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
        #self.receive_data()

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

        self.communication_service.send_message("HOLA")
        img = self.processing_service.capture_image()
        img_undistorted = self.processing_service.undistorted_image(img)
        df_filtrado, imagenresutado, residue_list = self.processing_service.detected_objects(img_undistorted, 0.2)
        self.processing_service.save_residue_list(residue_list)

        data = self.communication_service.receive_data()
        if data == "hola":
            resultJSON = self.generar_informacion(df_filtrado)
            print("Resultado de clasificación:", resultJSON)
            self.update_image(imagenresutado)
            self.reports.append(resultJSON)

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
        img = Image.fromarray(img)  # Asegúrate de que 'img' sea un array de numpy
        ctk_img = ctk.CTkImage(img, size=(400, 300))  # Ajusta el tamaño de la imagen según sea necesario
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img  # Guardar una referencia para evitar que la imagen sea recolectada por el garbage collector

    def update_reports(self):
        for widget in self.reports_scrollable_frame.winfo_children():
            widget.destroy()

        headers = ["ID", "Nombre", "Categoría", "Confianza", "Fecha"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(self.reports_scrollable_frame, text=header, fg_color="#5e5e5e", text_color="#ffffff")
            label.grid(row=0, column=col, padx=10, pady=5)

        reports = self.reports_service.get_all_rankings()
        for row_num, report in enumerate(reports, start=1):
            report_data = [report.id, report.nombre, report.categoria, report.confianza, report.fecha_deteccion]
            for col_num, data in enumerate(report_data):
                label = ctk.CTkLabel(self.reports_scrollable_frame, text=data, fg_color="#3e3e3e", text_color="#ffffff")
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
            label = ctk.CTkLabel(self.reports_scrollable_frame, text=header, fg_color="#5e5e5e", text_color="#ffffff")
            label.grid(row=0, column=col, padx=10, pady=5)

        for row_num, report in enumerate(reports, start=1):
            report_data = [report.id, report.nombre, report.categoria, report.confianza, report.fecha_deteccion]
            for col_num, data in enumerate(report_data):
                label = ctk.CTkLabel(self.reports_scrollable_frame, text=data, fg_color="#3e3e3e", text_color="#ffffff")
                label.grid(row=row_num, column=col_num, padx=10, pady=5)

    def update_statistics(self, reports):
        total_residues = len(reports)
        self.total_residues_label.configure(text=f"Total de Residuos: {total_residues}")

        categories = [report.categoria for report in reports]
        category_counts = {category: categories.count(category) for category in set(categories)}
        fig1, ax1 = plt.subplots()
        ax1.pie(category_counts.values(), labels=category_counts.keys(), autopct='%1.1f%%')
        ax1.axis('equal')
        self.update_figure(self.category_pie_chart, fig1)

        dates = [report.fecha_deteccion for report in reports]
        date_counts = {date: dates.count(date) for date in set(dates)}
        fig2, ax2 = plt.subplots()
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
                    print("Conexion establecida con exito")
                else:
                    print("Fallo la conexion", response)
            self.communication_service.send_and_receive("CONECTAR", "Conectado", handle_response)

