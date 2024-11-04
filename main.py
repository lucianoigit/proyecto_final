from app.esp_interface.View_HIM import View
from app.repositories.residue_repository import ResidueRepository
from app.services.IA_model_service import MLModelService
from app.services.reports_service import ReportsService
from app.services.serial_service import SerialService
from app.services.image_processing_service import ImageProcessingService
from app.services.transporter_service import TransportService
from database.db import Database
from picamera2 import Picamera2

DATABASE_URL = "sqlite:///./test.db"

def main():
    db = Database(DATABASE_URL)
    db.create_database()

    # Configuración para Raspberry Pi con el puerto serial adecuado
    SERIAL_PORT = '/dev/ttyUSB0'  # o '/dev/ttyAMA0' según la configuración del dispositivo
    BAUD_RATE = 115200

    # Inicializa la cámara sin configurarla todavía
    picam2 = Picamera2()
    
    with db.session() as session:
        residue_repository = ResidueRepository(session)
        serial_service = SerialService(SERIAL_PORT, BAUD_RATE)
  
        # Intentamos inicializar la comunicación serial
        serial_service.initialize_communication()
        ser = serial_service.getStatus()
        serial_service.send_and_receive("LED_ON","Light On",None)

        # Configuración del modelo y otros servicios
        use_model = MLModelService(model_path='./yolov5s.pt')
        reports_service = ReportsService(residue_repository)
        transport_service = TransportService()

        # Inicia el servicio de procesamiento de imágenes
        image_service = ImageProcessingService(residue_repository, use_model, transport_service, picamera=picam2)
        
        # Inicializa la aplicación principal
        app = View(serial_service, image_service, reports_service, transport_service, ser, picamera=picam2)
        app.mainloop()
        
        # Asegurar que los recursos se liberen correctamente
        picam2.stop()  # Detenemos la cámara al salir
        serial_service.close()  # Cerramos el servicio serial

if __name__ == "__main__":
    main()
