from app.esp_interface.View_HIM import View
from app.repositories.residue_repository import ResidueRepository

from app.services.IA_model_service import MLModelService
from app.services.reports_service import ReportsService
from app.services.serial_service import SerialService
from app.services.image_processing_service import ImageProcessingService
from database.db import Database
import serial

DATABASE_URL = "sqlite:///./test.db"

def main():
    db = Database(DATABASE_URL)
    db.create_database()

    SERIAL_PORT = 'COM4'
    BAUD_RATE = 115200
  
    
    with db.session() as session:
        residue_repository = ResidueRepository(session)
        serial_service = SerialService(SERIAL_PORT, BAUD_RATE)
        serial_service.initialize_communication()
        
        use_model = MLModelService(model_path='./yolov5s.pt')
        reports_service = ReportsService(residue_repository)
        image_service = ImageProcessingService(residue_repository, use_model)
        
        app = View(serial_service, image_service, reports_service)
        app.mainloop()

if __name__ == "__main__":
    main()
