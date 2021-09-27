from abc import ABC, abstractmethod


class AbstractEmailAdapter(ABC):
    @abstractmethod
    def send_mail(self, to: str, message: str):
        raise NotImplementedError


class FakeEmailAdapter(AbstractEmailAdapter):
    def send_mail(self, to: str, message: str):
        print(f"to: {to}. msg: {message}")
