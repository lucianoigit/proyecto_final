import serial
from app.abstracts.ICommunication import CommunicationInterface

class SerialService(CommunicationInterface):
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None

    def initialize_communication(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=0)
        except serial.SerialException as e:
            print("Error al abrir el puerto serial:", e)

    def send_message(self, message):
        if self.ser is not None and self.ser.is_open:
            self.ser.write(message.encode())
        else:
            print("El puerto serial no está disponible para enviar mensajes")

    def receive_data(self):
        if self.ser is not None and self.ser.is_open and self.ser.in_waiting:
            return self.ser.readline().decode().strip()
        return None
