from abc import ABC, abstractmethod

from utils.result import ResultType


class DetectionMethod(ABC):
    @abstractmethod
    async def run(self) -> ResultType:
        pass