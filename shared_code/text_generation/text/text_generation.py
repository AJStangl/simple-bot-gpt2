import gc
import random
from typing import Optional
import codecs
import logging
import os
import re
import time
import torch
import ftfy
from detoxify import Detoxify
from simpletransformers.language_generation import LanguageGenerationModel

from shared_code.handlers.image_generator import ImageGenerator
from shared_code.handlers.image_searching import ImageHandler


class ModelTextGenerator:
	def __init__(self, bot_name: str, use_cuda=False):
		# noinspection SpellCheckingInspection
		self.text_generation_parameters = {
			'max_length': 1024,
			'num_return_sequences': 1,
			'prompt': None,
			'temperature': 0.8,
			'top_k': 40,
			'repetition_penalty': 1.008,
			'stop_token': '<|endoftext|>'
		}
		self.devices = ['cuda:0', 'cuda:1']
		self.model_path: str = os.environ[f"{bot_name}"]
		self.model = LanguageGenerationModel("gpt2", self.model_path, use_cuda=use_cuda, cuda_device=random.randint(0, 1))
		self.detoxify = Detoxify('unbiased-small', device=torch.device(random.choice(self.devices) if use_cuda else 'cpu'))
		self.image_handler: ImageHandler = ImageHandler()

	@staticmethod
	def capture_tag(test_string: str, expected_tags=None):
		if expected_tags is None:
			expected_tags = ["<|eor|>", "<|eoopr|>", "<|eoocr|>"]
		regex = r"\<\|(.*)\|\>"

		matches = re.finditer(regex, test_string, re.MULTILINE)

		for matchNum, match in enumerate(matches, start=1):

			logging.debug(
				"Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
																				 end=match.end(), match=match.group()))

			for tag in expected_tags:
				if match.group() == tag:
					return_string = test_string.replace(match.group(), "")
					return return_string

	def generate_text(self, prompt: str):
		start_time = time.time()
		reply = None
		raw_response = None
		output_list = []
		attempts = 0
		while reply is None:
			samples = self.model.generate(prompt=prompt, args=self.text_generation_parameters, verbose=False)
			sample = samples[0]
			output_list.append(sample)
			if sample is None:
				continue
			text = sample.replace(prompt, "\n")
			logging.debug(f"Generated Text:\n{text}")
			escaped = ftfy.fix_text(codecs.decode(text, "unicode_escape"))
			cleaned = escaped.replace(r'\n', "\n")
			result = self.capture_tag(cleaned)
			if result is not None:
				finalized = re.sub(r'(<\|[\w/ ]*\|>)', ' ', result).strip()
				raw_response = text
				if self.ensure_non_toxic(finalized):
					reply = finalized
			attempts += 1
			if attempts > 10:
				break
			else:
				logging.info(f"Attempting Again...{attempts}")

		end_time = time.time()
		duration = round(end_time - start_time, 1)

		logging.info(f'{len(output_list)} sample(s) of text generated in {duration} seconds.')
		return reply, raw_response

	def generate_submission(self, sub: str, post_type: str) -> dict:
		if post_type == "text":
			return self._generate_text_post(sub)
		if post_type == "image":
			return self._generate_image_post(sub)
		elif post_type == "link":
			return self._generate_link_post(sub)

	def _generate_text_post(self, sub: str) -> dict:
		try:
			max_attempts = 5
			reply = None
			title_regex = r"<\|sot\|>(.+?)<\|eot\|>"
			text_body_regex = r"<\|sost\|>(.+?)<\|eost\|>"
			prompt: str = f"<|ososs r/{sub}|><|sot|>"
			while reply is None:
				for text in self.model.generate(prompt=prompt, args=self.text_generation_parameters, verbose=False):
					# noinspection PyBroadException
					try:
						if max_attempts == 0:
							return {}

						cleaned_text = text.replace(prompt, "<|sot|>")
						result = cleaned_text.split("<|eost|>")[0] + "<|eost|>"
						title = re.findall(title_regex, result)[0]
						body = re.findall(text_body_regex, result)[0]
						clean_body = self.clean_string(body)
						clean_title = self.clean_string(title)

						if clean_body.startswith("http") or clean_body.startswith("www"):
							continue
						if self._is_not_none_or_empty(clean_body, clean_title):
							result = {
								"title": clean_title,
								"selftext": clean_body,
								"type": "text"
							}
							return result
						else:
							max_attempts -= 1
							continue
					except Exception:
						max_attempts -= 1
						continue
		finally:
			torch.cuda.empty_cache()
			gc.collect()

	def _generate_link_post(self, sub: str) -> dict:
		try:
			max_attempt = 5
			while max_attempt > 0:
				generate_text_post = self._generate_text_post(sub)
				clean_title = generate_text_post.get("title")
				body = generate_text_post.get("selftext")
				if body is None or clean_title is None:
					logging.info("Failed to generate text post, trying again...")
					max_attempt -= 1
					continue

				image_url = self.image_handler.get_image_post(body=body)

				if self._is_not_none_or_empty(body, image_url):
					result = {
						"title": clean_title,
						"url": image_url,
						"type": "link"
					}
					return result
				else:
					logging.info("Failed to validate link submission, trying again...")
					max_attempt -= 1
					continue
		finally:
			torch.cuda.empty_cache()
			gc.collect()

	def _generate_image_post(self, sub: str) -> dict:
		try:
			max_attempt = 5
			while max_attempt > 0:
				generate_text_post = self._generate_text_post(sub)
				clean_title = generate_text_post.get("title")
				body = generate_text_post.get("selftext")
				if body is None or clean_title is None:
					logging.info("Failed to generate text post, trying again...")
					max_attempt -= 1
					continue

				image_path = ImageGenerator().create_image(clean_title)

				if self._is_not_none_or_empty(body, image_path):
					result = {
						"title": clean_title,
						"image_path": image_path,
						"type": "image"
					}
					return result
				else:
					logging.info("Failed to validate link submission, trying again...")
					max_attempt -= 1
					continue
		finally:
			torch.cuda.empty_cache()
			gc.collect()


	@staticmethod
	def _is_not_none_or_empty(input_text_1: str, input_text_2: str) -> bool:
		if input_text_1 is None or input_text_1 == "":
			return False
		if input_text_2 is None or input_text_2 == "":
			return False
		return True

	@staticmethod
	def clean_string(text) -> Optional[str]:
		try:
			escaped = ftfy.fix_text(codecs.decode(text, "unicode_escape"))
			cleaned = escaped.replace(r'\n', "\n")
			return cleaned
		except Exception as e:
			logging.error(e)
			return None

	def ensure_non_toxic(self, input_text: str) -> bool:
		"""
		Ensure that the generated text is not toxic
		:param input_text:
		:return: True if non-toxic, False if toxic
		"""
		threshold_map = {
			'toxicity': 0.80,
			'severe_toxicity':  0.80,
			'obscene': 0.80,
			'identity_attack': 0.80,
			'insult':  0.80,
			'threat': 0.80,
			'sexual_explicit': 1.0
		}

		results = self.detoxify.predict(input_text)

		for key in threshold_map:
			if results[key] > threshold_map[key]:
				logging.info(f"Detoxify: {key} score of {results[key]} is above threshold of {threshold_map[key]}")
				return False
			else:
				return True
