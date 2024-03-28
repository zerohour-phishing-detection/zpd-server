import random

from methods import DetectionMethod
from utils.logging import main_logger
from utils.result import ResultType
from utils.timing import TimeIt

logger = main_logger.getChild("methods.random")


class Random(DetectionMethod):
    """
    This is a test detection method that when runned it calculates a random result.
    It can be used to test the decision strategies.
    """

    async def run(self, *args, **kwargs) -> ResultType:
        """
        This method computes a random result.
        """

        with TimeIt("random detection method"):
            rand = random.randint(-1, 1)
            result = ResultType(rand)

            logger.info(f"[RESULT] {result.name} due to randomness.")

            return result
