from abc import ABC, abstractmethod
from enum import Enum, auto


# TODO this class might change, be deleted or moved
class DetectionMethods(Enum):
    ReverseImageSearch = auto()
    Test = auto()


# TODO this class might change, be deleted or moved
class DetectionMethod(ABC):
    @abstractmethod
    def test(self):
        pass
