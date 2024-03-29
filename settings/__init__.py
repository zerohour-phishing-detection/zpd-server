from abc import ABC, abstractmethod


class Settings(ABC):
    @staticmethod
    @abstractmethod
    def from_json(settings_json: object) -> "Settings":
        pass
