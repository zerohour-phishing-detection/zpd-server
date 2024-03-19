import itertools
import os
from typing import AsyncIterator

from google.cloud import vision

from logo_finders.base import LogoFinder
from search_engines.text.base import TextSearchEngine
from search_engines.text.google import GoogleTextSearchEngine

# Set environment variable for the Google Cloud Service Account Key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".gcloud_creds.json"

# The features that we want to annotate images with, i.e. just logo detection
FEATURES = [vision.Feature(type_=vision.Feature.Type.LOGO_DETECTION)]

class VisionLogoDetection(LogoFinder):
	"""
	A `LogoFinder` that uses Google Cloud Vision's Logo Detection API
	to find the brand names of logos in an image, and then uses text search engines
	to find associated domains.
	"""
	client: vision.ImageAnnotatorAsyncClient
	text_search: TextSearchEngine

	def __init__(self, text_search: TextSearchEngine = GoogleTextSearchEngine()):
		"""
		Initiates the instance and connects to the Google Cloud API.

		Note: make sure you call this within context of the same event loop,
		as it will error otherwise.
		"""
		super().__init__("vision_logo_detection")
		self.client = vision.ImageAnnotatorAsyncClient()
		self.text_search = text_search

	async def find(self, img_path) -> AsyncIterator[str]:
		"""Detects logos in the file."""

		self.logger.info("Starting Google Cloud Vision Logo Detection")

		# Read image
		with open(img_path, "rb") as image_file:
			content = image_file.read()
		image = vision.Image(content=content)

		# Make request to Google Cloud and get response
		request = vision.AnnotateImageRequest(image=image, features=FEATURES)
		responses = await self.client.batch_annotate_images(requests=[request])
		response = responses.responses[0]

		# Check for error
		if response.error.message:
			raise Exception(
				"{}\nFor more info on error messages, check: "
				"https://cloud.google.com/apis/design/errors".format(response.error.message)
			)

		# Collect results
		logo_names = [logo.description for logo in response.logo_annotations]

		self.logger.info(f'Detected {len(logo_names)} logo(s): {logo_names}')

		for logo_name in logo_names:
			# Look up each logo brand name on the text search engine to get a URL from it
			# Take top 3 search results
			for logo_url in itertools.islice(self.text_search.query(logo_name), 3):
				yield logo_url
