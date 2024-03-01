from abc import ABC, abstractmethod
from enum import Enum, auto


class DetectionMethods(Enum):
    ReverseImageSearch = auto()
    Test = auto()

class DetectionMethod(ABC):
    @abstractmethod
    def test(self):
        pass