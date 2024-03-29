from settings import Settings


class RandomSettings(Settings):
    seed: str

    def __init__(self, seed: str = ""):
        self.seed = seed

    def from_json(self, settings_json: object) -> "RandomSettings":
        seed = settings_json["seed"]
        print(seed)
        return RandomSettings(seed)
