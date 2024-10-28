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

    SERIAL_PORT = 'COM4'
    BAUD_RATE = 115200

    # Inicializa la cámara
    picam2 = Picamera2()
    picam2.configure(picam2.create_still_configuration(main={"size": (640, 480), "format": "RGB888"}))
    picam2.start()

    with db.session() as session:
        residue_repository = ResidueRepository(session)
        serial_service = SerialService(SERIAL_PORT, BAUD_RATE)
        serial_service.initialize_communication()
        ser = serial_service.getStatus()
        use_model = MLModelService(model_path='./yolov5s.pt')
        reports_service = ReportsService(residue_repository)

        transport_service = TransportService()
        image_service = ImageProcessingService(residue_repository, use_model, transport_service, picamera=picam2)
        
        app = View(serial_service, image_service, reports_service, transport_service, ser, picamera=picam2)
        app.mainloop()
        
        picam2.stop()  # Detenemos la cámara al salir
        del serial_service  

if __name__ == "__main__":
    main()
