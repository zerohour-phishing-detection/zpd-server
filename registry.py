from methods import DetectionMethod
from methods.dst import DST
from methods.random import Random
from settings import Settings
from settings.dst import DSTSettings
from settings.random import RandomSettings
from utils.decision import DecisionStrategy, Majority, Strict, Unanimous

DETECTION_METHODS: dict[str, DetectionMethod] = {
    "dst": DST(),
    "random": Random(),
}

DETECTION_METHODS_SETTINGS: dict[str, Settings] = {"dst": DSTSettings(), "random": RandomSettings()}

DECISION_STRATEGIES: dict[str, DecisionStrategy] = {
    "majority": Majority(),
    "unanimous": Unanimous(),
    "strict": Strict(),
}
