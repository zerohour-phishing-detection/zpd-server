from abc import ABC, abstractmethod

from utils.result import ResultType


class DecisionStrategy(ABC):
    @staticmethod
    @abstractmethod
    def decide(results: list[ResultType]) -> ResultType:
        pass


class Strict(DecisionStrategy):
    @staticmethod
    def decide(results: list[ResultType]) -> ResultType:
        """
        Given a list of results it computes the strict decision.
        """

        if results.count(ResultType.PHISHING) > 0:
            return ResultType.PHISHING
        elif results.count(ResultType.INCONCLUSIVE) > 0:
            return ResultType.INCONCLUSIVE
        return ResultType.LEGITIMATE


class Majority(DecisionStrategy):
    @staticmethod
    def decide(results: list[ResultType]) -> ResultType:
        """
        Given a list of results it computes the majority decision.
        """

        diff = results.count(ResultType.PHISHING) - results.count(ResultType.LEGITIMATE)
        return ResultType(max(-1, min(1, diff)))


class Unanimous(DecisionStrategy):
    @staticmethod
    def decide(results: list) -> ResultType:
        """
        Given a list of results it computes the unanimous decision.
        """

        length = len(results) - results.count(ResultType.INCONCLUSIVE)
        diff = results.count(ResultType.PHISHING) - results.count(ResultType.LEGITIMATE)

        if abs(diff) != length:
            return ResultType.INCONCLUSIVE

        return ResultType(max(-1, min(1, diff)))


DECISION_STRATEGIES: dict[str, DecisionStrategy] = {
    "strict": Strict(),
    "majority": Majority(),
    "unanimous": Unanimous(),
}
