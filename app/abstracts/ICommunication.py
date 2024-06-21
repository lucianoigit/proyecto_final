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
