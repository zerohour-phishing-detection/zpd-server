from enum import Enum, auto

from utils.result import ResultType


class DecisionStrategy(Enum):
    STRICT = auto()
    MAJORITY = auto()
    UNANIMOUS = auto()


def decide(strategy: DecisionStrategy, results: list[ResultType]) -> ResultType:
    """
    Given a decision strategy and a list of results, it computes the decision.
    """

    match strategy:
        case DecisionStrategy.STRICT:
            return _strict(results)
        case DecisionStrategy.MAJORITY:
            return _majority(results)
        case DecisionStrategy.UNANIMOUS:
            return _unanimous(results)
        case _:
            raise ValueError("Unknown decision strategy!")


def _strict(results: list[ResultType]) -> ResultType:
    """
    Given a list of results it computes the strict decision.
    """

    if results.count(ResultType.PHISHING) > 0:
        return ResultType.PHISHING
    elif results.count(ResultType.INCONCLUSIVE) > 0:
        return ResultType.INCONCLUSIVE
    return ResultType.LEGITIMATE


def _majority(results: list[ResultType]) -> ResultType:
    """
    Given a list of results it computes the majority decision.
    """
    
    diff = results.count(ResultType.PHISHING) - results.count(ResultType.LEGITIMATE)
    return ResultType(max(-1, min(1, diff)))


def _unanimous(results: list) -> ResultType:
    """
    Given a list of results it computes the unanimous decision.
    """

    length = len(results) - results.count(ResultType.INCONCLUSIVE)
    diff = results.count(ResultType.PHISHING) - results.count(ResultType.LEGITIMATE)

    if abs(diff) != length:
        return ResultType.INCONCLUSIVE

    return ResultType(max(-1, min(1, diff)))
