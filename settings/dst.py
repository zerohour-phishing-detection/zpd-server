from settings import Settings


class DSTSettings(Settings):
    # Which logo finder to use, `homebrew` is an alias for `reverse_logo_region_search` and `google_vision` for `vision_logo_detection`
    LOGO_FINDERS: dict[str:int] = {"homebrew": 0, "google_vision": 1}

    logo_finder: int

    def __init__(self, logo_finder: int = 0):
        self.logo_finder = logo_finder

    def from_json(self, settings_json: object) -> "DSTSettings":
        logo_finder = self.LOGO_FINDERS[settings_json["logo_finder"]]

        return DSTSettings(logo_finder)

    def to_json(self) -> object:
        return {"logo_finder": list(self.LOGO_FINDERS.keys())[self.logo_finder]}
