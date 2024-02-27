import proxyscrape
import threading

from utils.custom_logger import CustomLogger

class ProxyGetter():
    _main_logger = CustomLogger().main_logger
    _instance = None

    collector = proxyscrape.create_collector('default', 'https')
    proxy = collector.get_proxy({'anonymous' : True})

    def __new__(self):
        if self._instance is None:
            self._instance = super().__new__(self)
        return self._instance

    def get_proxy(self):
        return {'https' : f"{self.proxy.host}:{self.proxy.port}"}

    def new_proxy(self):
        threading.Thread(target=self._new_proxies).start()

    def _new_proxies(self):
        '''
            Gets a free anonymous proxy based in US
            - Free generally does not support Google
            - US because near default exit point of current VPN.
        '''
        self.proxy = self.collector.get_proxy({'code' : 'us', 'anonymous' : True})
        self._main_logger.info(f"Set proxy to: {self.proxy.host}")
