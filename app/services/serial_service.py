import serial
import threading
import time
import queue

class SerialService:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.read_thread = None
        self.running = False
        self.buffer = ""
        self.lock = threading.Lock()
        self.message_queue = queue.Queue()
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
        
        message += "\n"  # Asegúrate de que el mensaje tenga un salto de línea al final
        if self.ser and self.ser.is_open:
            self.ser.write(message.encode("utf-8"))
            print("Mensaje enviado:", message)
        else:
            print("El puerto serial no está disponible para enviar mensajes")


    def send_and_receive(self, message, expected_response, callback):
        self.send_message(message)
        def wait_for_response():
            start_time = time.time()
            while time.time() - start_time < 10:  # Período de espera
                try:
                    response = self.message_queue.get(timeout=10 - (time.time() - start_time))  # Intenta obtener un mensaje de la cola
                    print(f"expected_response: ", expected_response)
                    print(f"response:", response)
                    if expected_response.strip() == response.strip():
                        callback("OK")
                except queue.Empty:
                    pass
        threading.Thread(target=wait_for_response).start()



    # def send_and_receive(self, message, expected_response, callback):
    #     self.send_message(message)

    #     def wait_for_response():
    #         start_time = time.time()

    #         while time.time() - start_time < 10:
    #             try:
    #                 response = self.message_queue.get(timeout=10 - (time.time() - start_time))
    #                 if expected_response == response:
    #                     callback("OK")
    #                     return
    #             except queue.Empty:
    #                 pass
    #             callback("No response")
    #         #     self.response_event.wait(timeout=1)  # Espera de 1 segundo antes de verificar
    #         #     with self.lock:
    #         #         # Procesar el buffer para extraer y comparar el mensaje completo
    #         #         while '\n' in self.buffer:
    #         #             received_message, self.buffer = self.buffer.split('\n', 1)
    #         #             received_message = received_message.strip()
    #         #             if received_message == expected_response.strip():
    #         #                 callback("OK")
    #         #                 self.response_event.clear()  # Reiniciar el evento
    #         #                 return
    #         #     # Clear event and retry
    #         #     self.response_event.clear()

    #         # callback("Timeout")

    #     threading.Thread(target=wait_for_response).start()

    def receive_data(self):
        try:
            if self.ser and self.ser.is_open:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                    with self.lock:
                        self.buffer += data
                        # Procesar el buffer para extraer mensajes
                        while '\n' in self.buffer:
                            # pos = self.buffer.find('\n')
                            # line = self.buffer[:pos].split()
                            # self.buffer = self.buffer[pos + 1:]
                            # self.message_queue.put(line)

                            message, self.buffer = self.buffer.split('\n', 1)
                            if message.strip():  # Evitar procesar mensajes vacíos
                                self.message_queue.put(message)
                                print(f"Mensaje recibido: {message.strip()}")
                            
                            self.response_event.set()
                        # NOTIFICACION DE EVENTO
                        # self.response_event.set()
        except Exception as e:
            print(f"Error al recibir datos: {e}")

    def _reading_loop(self):
        while self.running:
            self.receive_data()

    def _start_reading(self):
        if not self.running:
            self.running = True
            self.read_thread = threading.Thread(target=self._reading_loop, daemon=True)
            self.read_thread.start()

    def _stop_reading(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join()

    def __del__(self):
        self._stop_reading()
        if self.ser:
            self.ser.close()
