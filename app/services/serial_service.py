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

    def initialize_communication(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Puerto serial {self.port} abierto correctamente.")
            if not self.running:
                self.start_reading()
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial {self.port}: {e}")

    def send_message(self, message):
        print("Mensaje enviado:", message)
        message += "\r\n"  # Asegúrate de usar el mismo fin de línea que Arduino
        if self.ser and self.ser.is_open:
            self.ser.write(message.encode("utf-8"))
        else:
            print("El puerto serial no está disponible para enviar mensajes")

    
    def receive_data(self):
        try:
            if self.ser and self.ser.is_open:
                if self.ser.in_waiting > 0:  # Verifica si hay datos disponibles
                    data = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                    if data:
                        self.buffer += data
                        print(f"Datos en bruto: {data}")
                        if "\n" in self.buffer:  # Revisa el fin de línea adecuado
                            messages = self.buffer.split("\n")
                            self.buffer = messages.pop()  # Guarda cualquier fragmento incompleto
                            if messages:
                                return messages  # Devuelve solo el primer mensaje completo
        except Exception as e:
            print(f"Error al recibir datos: {e}")
        return ""


    def start_reading(self):
        if not self.running:
            self.running = True
            self.read_thread = threading.Thread(target=self.reading_loop, daemon=True)
            self.read_thread.start()

    def stop_reading(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join()

    def reading_loop(self):
        while self.running:
            messages = self.receive_data()
            for message in messages:
                print("Recibido:", message)
            time.sleep(0.1)

    def __del__(self):
        self.stop_reading()
        if self.ser:
            self.ser.close()
