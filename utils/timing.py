import time

from utils.logging import main_logger

logger = main_logger.getChild('utils.timing')


class TimeIt:
    start: float
    title: str
    unit: str  # 's' or 'ms'

    def __init__(self, title=None, unit="ms"):
        self.title = title
        self.unit = unit

        if unit not in ["s", "ms"]:
            raise ValueError("unknown unit: " + unit)

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        end = time.time()
        diff = end - self.start

        title = self.title
        if title is None:
            title = "Component"

        unit = self.unit
        if unit == "ms":
            diff *= 1000

        logger.info("[TIMING] %s took %.3f%s", title, diff, unit)


if __name__ == "__main__":
    print("before")
    with TimeIt("abc"):
        [x * x for x in range(10000000)]
        print("inside")
    print("after")
