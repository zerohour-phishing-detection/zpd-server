from engines.bing import BingReverseImageSearchEngine
from engines.tineye import TinEyeReverseImageSearchEngine
from engines.google import GoogleReverseImageSearchEngine
from engines.yandex import YandexReverseImageSearchEngine
from engines.bing import BingReverseImageSearchEngine

# Setup logging
from utils.custom_logger import CustomLogger

class SearchEngine:
    _main_logger = CustomLogger().main_logger

    _instance = None

    _google = GoogleReverseImageSearchEngine()
    _yandex = YandexReverseImageSearchEngine()
    _tineye = TinEyeReverseImageSearchEngine()
    _bing = BingReverseImageSearchEngine()

    def __new__(self):
        if self._instance is None:
            self._instance = super().__new__(self)
        return self._instance

    def get_identifiers(self):
        return ['all', *(self._google.identifiers()), *(self._yandex.identifiers()), *(self._tineye.identifiers())]

    def get_engine(self, identifier:str) -> list:
        if identifier in self._google.identifiers():
            return [self._google]
        elif identifier in self._yandex.identifiers():
            return [self._yandex]
        elif identifier in self._tineye.identifiers():
            return [self._tineye]
        elif identifier in self._bing.identifiers():
            return [self._bing]
        elif identifier == 'all':
            return [self._google, self._yandex]
        else:
            raise NotImplementedError
