from enum import Enum

class Result(Enum):
    LEGITIMATE = -1
    INCONCLUSIVE = 0
    PHISHING = 1

def majority(results : list[Result]) -> Result:
    """
    Given a list of results it computes the majority decision.
    """
    
    diff = results.count(Result.PHISHING) - results.count(Result.LEGITIMATE)
    return Result(max(-1, min(1, diff)))
    
def unanimous(results : list) -> Result:
    """
    Given a list of results it computes the unanimous decision.
    """
    
    length = len(results) - results.count(Result.INCONCLUSIVE)
    diff = results.count(Result.PHISHING) - results.count(Result.LEGITIMATE)
    
    if abs(diff) != length:
        return Result.INCONCLUSIVE
    
    return Result(max(-1, min(1, diff)))