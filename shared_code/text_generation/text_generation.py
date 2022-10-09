import codecs
import logging
import os
import re
import time

import ftfy
from simpletransformers.language_generation import LanguageGenerationModel


class ModelTextGenerator:
	def __init__(self, bot_name: str):
		self.text_generation_parameters = {
			'max_length': 1024,
			'num_return_sequences': 1,
			'prompt': None,
			'temperature': 0.8,
			'top_k': 40,
			'repetition_penalty': 1.008,
			'stop_token': '<|endoftext|>'
		}
		self.model_path: str = os.environ[f"{bot_name}"]
		self.model = LanguageGenerationModel("gpt2", self.model_path, use_cuda=False)

	@staticmethod
	def capture_tag(test_string: str, expected_tags: [str] = ["<|eor|>", "<|eoopr|>", "<|eoocr|>"]):
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

			# for groupNum in range(0, len(match.groups())):
			# 	groupNum = groupNum + 1
			#
			# 	logging.debug("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum,
			# 																	start=match.start(groupNum),
			# 																	end=match.end(groupNum),
			# 																	group=match.group(groupNum)))

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

	def generate_text_post(self, sub: str) -> dict:
		reply = None
		title_regex = r"<\|sot\|>(.+?)<\|eot\|>"
		text_body_regex = r"<\|sost\|>(.+?)<\|eost\|>"
		prompt: str = f"<|ososs r/{sub}|><|sot|>"
		while reply is None:
			for text in self.model.generate(prompt=prompt, args=self.text_generation_parameters, verbose=False):
				cleaned_text = text.replace(prompt, "<|sot|>")
				result = cleaned_text.split("<|eost|>")[0] + "<|eost|>"
				title = re.findall(title_regex, result)[0]
				body = re.findall(text_body_regex, result)[0]
				clean_body = self.clean_string(body)
				clean_title = self.clean_string(title)
				result = {
					"title": clean_title,
					"selftext": clean_body
				}
				return result

	def clean_string(self, text):
		try:
			escaped = ftfy.fix_text(codecs.decode(text, "unicode_escape"))
			cleaned = escaped.replace(r'\n', "\n")
			return cleaned
		except Exception as e:
			logging.error(e)
			return None