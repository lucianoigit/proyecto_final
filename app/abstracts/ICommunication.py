from abc import ABC, abstractmethod

class CommunicationInterface(ABC):
    @abstractmethod
    def initialize_communication(self):
        pass

    @abstractmethod
    def send_message(self, message):
        pass

    @abstractmethod
    def receive_data(self):
        pass
    @abstractmethod
    def getStatus(self):
        pass
    @abstractmethod
    def start_reading(self):
        pass

    @abstractmethod
    def stop_reading(self):
        pass

    @abstractmethod
    def send_and_receive(self,message,expected_message):
        pass
