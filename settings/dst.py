from settings import Settings


class DSTSettings(Settings):
    def __init__(self) -> None:
        super().__init__()

    def from_json(self, settings_json: object) -> "DSTSettings":
        return DSTSettings()
