from settings import Settings


class DSTSettings(Settings):
    # Which logo finder to use, `homebrew` for the orignial logo detection service and `gcv`(Google Cloud Vision) for `vision_logo_detection`
    LOGO_FINDERS: dict[str:int] = {"homebrew": 0, "gcv": 1}

    logo_finder: int
    text_search_results: int
    s_sim_1: float
    s_sim_2: float
    emd_1: float
    emd_2: float
    homebrew_regions: int
    homebrew_search_results: int
    gcv_top_results: int

    def __init__(
        self,
        logo_finder: int = 0,
        text_search_results: int = 7,
        s_sim_1: float = 0.7,
        s_sim_2: float = 0.8,
        emd_1: float = 0.001,
        emd_2: float = 0.002,
        hombrew_regions: int = 3,
        homebrew_search_results: int = 7,
        gcv_top_results: int = 3,
    ):
        self.logo_finder = logo_finder
        self.text_search_results = text_search_results
        self.s_sim_1 = s_sim_1
        self.s_sim_2 = s_sim_2
        self.emd_1 = emd_1
        self.emd_2 = emd_2
        self.homebrew_regions = hombrew_regions
        self.homebrew_search_results = homebrew_search_results
        self.gcv_top_results = gcv_top_results

    def from_json(self, settings_json: object) -> "DSTSettings":
        logo_finder = self.LOGO_FINDERS[settings_json["logo_finder"]]
        text_search_results = settings_json["text_search_results"]
        s_sim_1 = settings_json["s_sim_1"]
        s_sim_2 = settings_json["s_sim_2"]
        emd_1 = settings_json["emd_1"]
        emd_2 = settings_json["emd_2"]
        homebrew_regions = settings_json["homebrew_regions"]
        homebrew_search_results = settings_json["homebrew_search_results"]
        gcv_top_results = settings_json["gcv_top_results"]

        return DSTSettings(
            logo_finder,
            text_search_results,
            s_sim_1,
            s_sim_2,
            emd_1,
            emd_2,
            homebrew_regions,
            homebrew_search_results,
            gcv_top_results,
        )

    def to_json(self) -> object:
        return {
            "logo_finder": list(self.LOGO_FINDERS.keys())[self.logo_finder],
            "text_search_results": self.text_search_results,
            "s_sim_1": self.s_sim_1,
            "s_sim_2": self.s_sim_2,
            "emd_1": self.emd_1,
            "emd_2": self.emd_2,
            "homebrew_regions": self.homebrew_regions,
            "homebrew_search_results": self.homebrew_search_results,
            "gcv_top_results": self.gcv_top_results,
        }
