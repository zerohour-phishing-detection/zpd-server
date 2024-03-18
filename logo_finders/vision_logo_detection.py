import itertools
from typing import AsyncIterator

from google.cloud import vision

from logo_finders.base import LogoFinder
from search_engines.text.google import GoogleTextSearchEngine

features = [vision.Feature(type_=vision.Feature.Type.LOGO_DETECTION)]

class VisionLogoDetection(LogoFinder):
	client: vision.ImageAnnotatorAsyncClient

	def __init__(self):
		super().__init__("vision_logo_detection")
		self.client = vision.ImageAnnotatorAsyncClient()

	async def find(self, img_path) -> AsyncIterator[str]:
		"""Detects logos in the file."""

		with open(img_path, "rb") as image_file:
			content = image_file.read()

		image = vision.Image(content=content)

		request = vision.AnnotateImageRequest(image=image, features=features)
		responses = await self.client.batch_annotate_images(requests=[request])
		response = responses.responses[0]

		if response.error.message:
			raise Exception(
				"{}\nFor more info on error messages, check: "
				"https://cloud.google.com/apis/design/errors".format(response.error.message)
			)

		logo_names = response.logo_annotations

		g = GoogleTextSearchEngine()

		self.logger.info(f'Detected {len(logo_names)} logos')

		for logo in logo_names:
			logo_name = logo.description
			self.logger.info(f'Found logo origin: {logo_name}')
			
			for logo_url in itertools.islice(g.query(logo_name), 7):
				yield logo_url
		