import serial
import cv2
import numpy as np
import os
import glob
import customtkinter as ctk
import torch
import time
import json

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200
MAX_ATTEMPTS = 10

class ESPInterface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Delta Robot")
        self.ser = None  
        self.text_box = None
        self.message_entry = None
        self.config_entry = None
        self.calibracion = False
        self.contador_calibracion = 0
        self.mtx = 0
        self.dist = 0

        self.initialize_serial()
        self.create_widgets()
        self.receive_data()

    def initialize_serial(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0)
        except serial.SerialException as e:
            print("Error al abrir el puerto serial:", e)

    def create_widgets(self):
        # Marco para los controles del lado izquierdo
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.text_box = ctk.CTkTextbox(left_frame, height=10, width=40)
        self.text_box.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        self.message_entry = ctk.CTkEntry(left_frame)
        self.message_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        send_button = ctk.CTkButton(left_frame, text="Enviar", command=self.send_message)
        send_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        classify_button = ctk.CTkButton(left_frame, text="Iniciar Clasificación", command=self.clasificacion)
        classify_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        take_photo_button = ctk.CTkButton(left_frame, text="Tomar Foto", command=self.tomar_foto)
        take_photo_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        #classify_photo_button = ctk.CTkButton(left_frame, text="Clasificar Foto", command=self.clasificar_foto)
        #classify_photo_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        calibrate_button = ctk.CTkButton(left_frame, text="Calibrar", command=self.calibrate)
        calibrate_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Marco para la imagen con la clasificación
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        #self.clasification_image = ctk.CTkImage(right_frame)
        #self.clasification_image.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def receive_data(self):
        if self.ser is not None and self.ser.is_open and self.ser.in_waiting:
            received_data = self.ser.readline().decode().strip()
            self.text_box.insert(ctk.END, "{}\n".format(received_data))
            self.text_box.see(ctk.END)
        self.after(100, self.receive_data)

    def send_message(self):
        if self.ser is not None and self.ser.is_open:
            message = self.message_entry.get() + '\n'
            self.ser.write(message.encode())
            self.message_entry.delete(0, ctk.END)
        else:
            print("El puerto serial no está disponible para enviar mensajes")

    def clasificacion(self):
        if not self.calibracion:
            self.mtx, self.dist = self.calibrate(dirpath="./calibracion", prefix="tablero-ajedrez", image_format="jpg", square_size=30, width=7, height=7)

        if self.ser is None or not self.ser.is_open:
            print("El puerto serial no está disponible para la clasificación")
            return

        self.ser.write("¿Estás listo?\n".encode())
        img = self.tomar_foto()
        img_undistorted = self.undistort_image(img)
        df_filtrado, imagenresutado = self.detectar_objetos(img_undistorted)
        start_time = time.time()
        while True:
            if self.ser.in_waiting:
                respuesta = self.ser.readline().decode().strip()
                if respuesta == "OK":
                    resultJSON = self.generar_informacion(df_filtrado)
                    print("Resultado de clasificación:", resultJSON)
                    break
            if time.time() - start_time > 30:
                print("No se recibió respuesta 'OK' después de 30 segundos. Volviendo a intentar...")
                start_time = time.time()

    def detectar_objetos(self, img_undistorted, confianza_minima=0.2, tamano_entrada=(416, 416)):
        print("Iniciando detección de objetos")
        try:
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
            resultados = model(img_undistorted)
            imagenresutado = resultados.show()
            df = resultados.pandas().xyxy[0]
            df_filtrado = df[df['confidence'] >= confianza_minima]
            df_filtrado['x_center'] = (df_filtrado['xmin'] + df_filtrado['xmax']) / 2
            df_filtrado['y_center'] = (df_filtrado['ymin'] + df_filtrado['ymax']) / 2
            return df_filtrado, imagenresutado
        except Exception as e:
            print(f"Error al detectar objetos: {e}")
            return [], None

    def tomar_foto(self):
        print("Tomando fotografía")
        cam = cv2.VideoCapture(0)
        
        # Tomar una foto
        ret, foto = cam.read()

        # Liberar la cámara
        cam.release()

        return foto

    def undistort_image(self, img):
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
        img_undistorted = cv2.undistort(img, self.mtx, self.dist, None, newcameramtx)
        return img_undistorted

    def calibrate(self, dirpath, prefix, image_format, square_size, width, height):
        print("Llega al glob")
        images = glob.glob(f"{dirpath}/{prefix}*.{image_format}")
        print("Nombre de las imágenes", images)
        objp = np.zeros((width * height, 3), np.float32)
        objp[:, :2] = np.mgrid[0:width, 0:height].T.reshape(-1, 2) * square_size

        objpoints = []
        imgpoints = []

        for fname in images:
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            ret, corners = cv2.findChessboardCorners(gray, (width, height), None)

            if ret:
                objpoints.append(objp)
                imgpoints.append(corners)
    
        if not objpoints or not imgpoints:
            print("No se encontraron imágenes válidas para la calibración.")
            return None, None

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

        return mtx, dist
    

if __name__ == "__main__":
    app = ESPInterface()
    app.mainloop()
