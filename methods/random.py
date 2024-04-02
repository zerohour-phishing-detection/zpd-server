import random

from methods import DetectionMethod
from settings.random import RandomSettings
from utils.logging import main_logger
from utils.result import ResultType

logger = main_logger.getChild("methods.random")


class Random(DetectionMethod):
    """
    This is a test detection method that when runned it calculates a random result.
    It can be used to test the decision strategies.
    """

    async def run(self, a, b, c, settings: RandomSettings) -> ResultType:
        """
        This method computes a random result.
        """

        if settings.seed != "":
            random.seed(settings.seed)

        rand = random.randint(-1, 1)

        result = ResultType(rand)

        logger.info(f"[RESULT] {result.name} due to randomness.")

        return result
