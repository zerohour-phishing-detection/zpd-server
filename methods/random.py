import random

from methods import DetectionMethod
from utils.result import ResultType


class Random(DetectionMethod):
    """
    This is a test detection method that when runned it calculates a random result.
    It can be used to test the decision strategies.
    """

    async def run(self, *args, **kwargs) -> ResultType:
        """
        This method computes a random result.
        """

        rand = random.randint(-1, 1)
        return ResultType(rand)
