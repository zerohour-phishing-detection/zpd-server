from methods import DetectionMethod
from methods.dst import DST
from methods.random import Random
from utils.decision import DecisionStrategy, Majority, Strict, Unanimous

DETECTION_METHODS: dict[str, DetectionMethod] = {
    "dst": DST(),
    "random": Random(),
}

DECISION_STRATEGIES: dict[str, DecisionStrategy] = {
    "strict": Strict(),
    "majority": Majority(),
    "unanimous": Unanimous(),
}
