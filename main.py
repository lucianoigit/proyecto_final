from app.esp_interface.View_HIM import View
from app.services.serial_service import SerialService
from app.services.image_processing_service import ImageProcessingService


if __name__ == "__main__":
    SERIAL_PORT = 'COM5'
    BAUD_RATE = 115200


    serial_service = SerialService(SERIAL_PORT, BAUD_RATE)
    image_service = ImageProcessingService()
    app = View(serial_service, image_service)
    app.mainloop()
