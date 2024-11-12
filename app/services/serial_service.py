
import serial
import threading
import time
import queue

class SerialService:
    def __init__(self, port, baud_rate):
        self.port = port
        self.isOpen = False
        self.baud_rate = baud_rate
        self.ser = None
        self.read_thread = None
        self.running = False
        self.buffer = ""
        self.lock = threading.Lock()
        self.message_queue = queue.Queue()  # Para almacenar mensajes recibidos
        self.response_event = threading.Event()

    def initialize_communication(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Puerto serial {self.port} abierto correctamente.")
            if not self.running:
                self._start_reading()  # Iniciar el hilo de lectura
                self.isOpen = True
        except serial.SerialException as e:
            print(f"Error al abrir el puerto serial {self.port}: {e}")

    def send_message(self, message):
        """Envía un mensaje por el puerto serial."""
        message += "\n"  # Asegúrate de que el mensaje tenga un salto de línea al final
        if self.ser and self.ser.is_open:
            self.ser.write(message.encode("utf-8"))
            print(f"Mensaje enviado: {message}")
        else:
            print("El puerto serial no está disponible para enviar mensajes.")

    def send_and_receive(self, message, expected_response, callback):
        """
        Envía un mensaje por el puerto serial y espera por una respuesta específica.
        La espera es indefinida hasta recibir la respuesta esperada.
        """
        self.send_message(message)
        print(f"Esperando respuesta para el mensaje: {message}")

        while True:  # Bucle infinito hasta recibir la respuesta esperada
            try:
                # Bloquea indefinidamente hasta que haya un mensaje en la cola
                response = self.message_queue.get()  
                print(f"expected_response: {expected_response}")
                print(f"response: {response}")

                if expected_response.strip() == response.strip():
                    callback("OK")
                    return  # Finalizamos si encontramos la respuesta esperada
            except Exception as e:
                print(f"Error al recibir respuesta: {e}")
                callback("Error")
                return

    def get_data(self, message, callback):
        """
        Envía un mensaje por el puerto serial y espera una respuesta cualquiera.
        No verifica si la respuesta coincide con algún valor esperado.
        """
        self.send_message(message)
        print(f"Mensaje enviado: {message}, esperando cualquier respuesta...")

        try:
            # Bloquear y esperar hasta que haya un mensaje en la cola
            response = self.message_queue.get(timeout=5)  # Espera hasta 5 segundos para recibir una respuesta
            print(f"Respuesta recibida: {response}")
            callback(response)  # Llama al callback con la respuesta recibida
        except queue.Empty:
            print("No se recibió ninguna respuesta en el tiempo esperado.")
            callback("No response")
        except Exception as e:
            print(f"Error al recibir datos: {e}")
            callback("Error")

    def receive_data(self):
        """
        Método llamado por el hilo de lectura para recibir datos del puerto serial.
        Procesa el buffer y añade los mensajes a la cola.
        """
        try:
            if self.ser and self.ser.is_open:
                if self.ser.in_waiting > 0:  # Si hay datos en el buffer del puerto serial
                    data = self.ser.read(self.ser.in_waiting).decode("utf-8", errors="replace")
                    with self.lock:
                        self.buffer += data

                        # Procesar el buffer para extraer mensajes completos
                        while '\n' in self.buffer:
                            message, self.buffer = self.buffer.split('\n', 1)
                            message = message.strip()
                            if message:  # Evitar mensajes vacíos
                                self.message_queue.put(message)  # Añadir el mensaje completo a la cola
                                print(f"Mensaje recibido: {message}")
        except Exception as e:
            print(f"Error al recibir datos: {e}")

    def _reading_loop(self):
        """Hilo dedicado para la lectura continua del puerto serial."""
        while self.running:
            self.receive_data()
            time.sleep(0.1)  # Evitar uso intensivo del CPU

    def _start_reading(self):
        """Inicia el hilo dedicado para la lectura del puerto serial."""
        if not self.running:
            self.running = True
            self.read_thread = threading.Thread(target=self._reading_loop, daemon=True)
            self.read_thread.start()

    def _stop_reading(self):
        """Detiene el hilo de lectura."""
        self.running = False
        if self.read_thread:
            self.read_thread.join()

    def close(self):
        """Cierra el puerto serial y detiene el hilo de lectura."""
        self._stop_reading()
        if self.ser:
            self.ser.close()
            self.isOpen = False
            print(f"Puerto serial {self.port} cerrado correctamente.")
            
    def getStatus(self):
        return self.isOpen

    def __del__(self):
        self.close()  # Asegurar que se cierra el puerto serial cuando se destruye la instancia