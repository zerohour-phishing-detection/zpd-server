import random
from abc import ABC, abstractmethod
from enum import Enum

from methods.reverse_image_search_method import ReverseImageSearchMethod
from utils.result import ResultType


class DetectionMethod(ABC):
    @abstractmethod
    def run(self) -> ResultType:
        pass


class TestMethod(DetectionMethod):
    """
    This is a test detection method that when runned it calculates a random result.
    It can be used to test the decision strategies.
    """

    def run(self, *args, **kwargs) -> ResultType:
        """
        This method computes a random result.
        """

        rand = random.randint(-1, 1)
        return ResultType(rand)


class DetectionMethods(Enum):
    ReverseImageSearch = ReverseImageSearchMethod()
    Test = TestMethod()
