import serial
import threading
import time

class SerialService:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.read_thread = None
        self.running = False
        self.buffer = ""
        self.lock = threading.Lock()
        self.response_event = threading.Event()

    def initialize_communication(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Puerto serial {self.port} abierto correctamente.")
            if not self.running:
                self._start_reading()
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial {self.port}: {e}")

    def send_message(self, message):
        print("Mensaje enviado:", message)
        message += "\r\n"
        if self.ser and self.ser.is_open:
            self.ser.write(message.encode("utf-8"))
        else:
            print("El puerto serial no está disponible para enviar mensajes")

    def send_and_receive(self, message, expected_response, callback):
        self.send_message(message)
        def wait_for_response():
            if self.response_event.wait(timeout=10): # ESPERA AL EVENTO O LO ELIMINA
                with self.lock:
                    if expected_response in self.buffer:
                        self.buffer = ""
                        callback("OK")
                    else:
                        callback("No response")
                self.response_event.clear()
            else:
                callback("Timeout")
        threading.Thread(target=wait_for_response).start()


    def receive_data(self):
        try:
            if self.ser and self.ser.is_open:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                    with self.lock:
                        self.buffer += data
                        print(f"Datos en bruto: {data}")
                        # NOTIFICACION DE EVENTO
                        self.response_event.set()
        except Exception as e:
            print(f"Error al recibir datos: {e}")

    def _start_reading(self):
        if not self.running:
            self.running = True
            self.read_thread = threading.Thread(target=self._reading_loop, daemon=True)
            self.read_thread.start()

    def _stop_reading(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join()

    def _reading_loop(self):
        while self.running:
            self.receive_data()
  

    def __del__(self):
        self._stop_reading()
        if self.ser:
            self.ser.close()
