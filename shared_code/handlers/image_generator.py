from typing import Optional
import logging
import torch
import gc
from diffusers import StableDiffusionPipeline


class ImageGenerator(object):
	def __init__(self):
		pass

	def create_image(self, prompt: str) -> Optional[str]:
		try:
			pipe: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained("/models/SexyStableDiffusion",
																					revision="fp16",
																					torch_dtype=torch.float16,
																					safety_checker=None)
			pipe = pipe.to("cuda")

			image = pipe(prompt, height=512, width=512, guidance_scale=20, num_inference_steps=200).images[0]

			image.save("/images/image.png")

			return "/images/image.png"

		except Exception as e:
			logging.info("Failed to generate image, trying again...")
			return None

		finally:
			logging.info("Image generated successfully!")
			try:
				torch.cuda.empty_cache()
				gc.collect()
			except Exception as e:
				logging.info("Failed to empty cache")
				gc.collect()
