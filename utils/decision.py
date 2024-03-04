from enum import Enum, auto

from utils.result import ResultTypes


class DecisionStrategies(Enum):
    Strict = auto()
    Majority = auto()
    Unanimous = auto()

def decide(strategy: DecisionStrategies, results: list[ResultTypes]) -> ResultTypes:
    """
    Given a decision strategy and a list of results, it computes the decision.
    """

    match strategy:
        case DecisionStrategies.Strict:
            return _strict(results)
        case DecisionStrategies.Majority:
            return _majority(results)
        case DecisionStrategies.Unanimous:
            return _unanimous(results)
        case _:
            raise ValueError("Unknown decision strategy!")


def _strict(results: list[ResultTypes]) -> ResultTypes:
    """
    Given a list of results it computes the strict decision.
    """

    if results.count(ResultTypes.PHISHING) > 0:
        return ResultTypes.PHISHING
    elif results.count(ResultTypes.INCONCLUSIVE) > 0:
        return ResultTypes.INCONCLUSIVE
    ResultTypes.LEGITIMATE


def _majority(results: list[ResultTypes]) -> ResultTypes:
    """
    Given a list of results it computes the majority decision.
    """

    diff = results.count(ResultTypes.PHISHING) - results.count(ResultTypes.LEGITIMATE)
    return ResultTypes(max(-1, min(1, diff)))


def _unanimous(results: list) -> ResultTypes:
    """
    Given a list of results it computes the unanimous decision.
    """

    length = len(results) - results.count(ResultTypes.INCONCLUSIVE)
    diff = results.count(ResultTypes.PHISHING) - results.count(ResultTypes.LEGITIMATE)

    if abs(diff) != length:
        return ResultTypes.INCONCLUSIVE

    return ResultTypes(max(-1, min(1, diff)))