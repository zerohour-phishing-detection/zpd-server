from settings import Settings


class RandomSettings(Settings):
    seed: str

    def __init__(self, seed: str = ""):
        self.seed = seed

    def from_json(self, settings_json: object) -> "RandomSettings":
        seed = settings_json["seed"]
        return RandomSettings(seed)

    def to_json(self) -> object:
        return {"seed": self.seed}
