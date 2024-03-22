import abc
import logging
from typing import AsyncIterator

from utils.logging import main_logger


class LogoFinder(abc.ABC):
	"""
	Find the origin of webpage screenshots by searching in the screenshot
	for visual features (such as logos) and finding their origin online.
	"""
	name: str
	logger: logging.Logger
	
	def __init__(self, name: str):
		"""
		Instantiate a new logo finder.

		Parameters
		----------
		name: str
			The (unique) name of the logo finder.
		"""
		self.name = name
		self.logger = main_logger.getChild(f'logo_finder.{name}')
	
	@abc.abstractmethod
	async def find(self, img_path) -> AsyncIterator[str]:
		"""
        Attempts to find logos (and their origins) in the image specified by the given path.

        Yields
        ------
        str
            The URL where it found the logo back online.
        """
		pass
