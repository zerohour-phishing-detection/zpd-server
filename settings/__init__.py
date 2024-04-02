from abc import ABC, abstractmethod


class Settings(ABC):
    """
    The abstract Settings class.
    """

    @staticmethod
    @abstractmethod
    def from_json(settings_json: object) -> "Settings":
        """
        Static method used to convert a JSON object to a Settings object.
        """

        pass
