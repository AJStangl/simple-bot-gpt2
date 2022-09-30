import os
import time
import logging
from simpletransformers.language_generation import LanguageGenerationModel
import re

class ModelTextGenerator:
	def __init__(self):
		self.text_generation_parameters = {
			'max_length': 1024,
			'num_return_sequences': 1,
			'prompt': None,
			'temperature': 0.8,
			'top_k': 40,
			'repetition_penalty': 1.008,
			'stop_token': '<|endoftext|>'
		}
		self.model_path: str = os.environ["Model"]
		self.model = LanguageGenerationModel("gpt2", self.model_path, use_cuda=False)

	def capture_tag(self, test_string: str, expected_tags: [str] = ["<|eor|>", "<|eoopr|>"]):
		regex = r"\<\|(.*)\|\>"

		matches = re.finditer(regex, test_string, re.MULTILINE)

		for matchNum, match in enumerate(matches, start=1):

			print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
																				end=match.end(), match=match.group()))

			if match.group() == expected_tags[0]:
				return_string = test_string.replace(match.group(), "")
				return return_string

			for groupNum in range(0, len(match.groups())):
				groupNum = groupNum + 1

				print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum,
																				start=match.start(groupNum),
																				end=match.end(groupNum),
																				group=match.group(groupNum)))

	def generate_text(self, prompt: str):
		start_time = time.time()

		reply = None
		output_list = []
		while reply is None:
			samples = self.model.generate(prompt=prompt, args=self.text_generation_parameters)
			sample = samples[0]
			output_list.append(sample)
			if sample is None:
				continue
			text = sample.replace(prompt, "\n")
			result = self.capture_tag(text)
			cleaned = result.replace(r'\n\n', "\n\n")
			if result is not None:
				reply = cleaned

		end_time = time.time()
		duration = round(end_time - start_time, 1)

		logging.info(f'{len(output_list)} sample(s) of text generated in {duration} seconds.')
		return reply