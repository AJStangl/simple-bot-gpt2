from typing import Optional
import logging
import torch
import gc
from diffusers import StableDiffusionPipeline


class ImageGenerator(object):
	def __init__(self):
		self.pipe: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained("/models/StableDiffusionPipeline", revision="fp16",
															torch_dtype=torch.float16, safety_checker=None)

	def create_image(self, prompt: str) -> Optional[str]:
		try:
			self.pipe = self.pipe.to("cuda")

			image = self.pipe(prompt).images[0]

			image.save("/images/image.png")

			return "/images/image.png"

		except:
			logging.info("Failed to generate image, trying again...")
			return None

		finally:
			logging.info("Image generated successfully!")
			torch.cuda.empty_cache()
			gc.collect()
