import random
from abc import ABC, abstractmethod
from enum import Enum

from methods.reverse_image_search_method import ReverseImageSearchMethod
from utils.result import ResultTypes


class DetectionMethod(ABC):
    @abstractmethod
    def test(self) -> ResultTypes:
        pass


class TestMethod(DetectionMethod):
    def test(self, *args, **kwargs):
        rand = random.randint(-1, 1)
        print(f"Test method result: {rand}")
        return ResultTypes(rand)

class DetectionMethods(Enum):
    ReverseImageSearch = ReverseImageSearchMethod()
    Test = TestMethod()


