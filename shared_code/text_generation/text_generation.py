import os
import time
import logging
from simpletransformers.language_generation import LanguageGenerationModel
from transformers import GPT2LMHeadModel, GPT2Tokenizer


class ModelTextGenerator:
	def __init__(self):
		self.text_generation_parameters = {
			'max_length': 1024,
			'num_return_sequences': 1,
			'prompt': None,
			'temperature': 0.8,
			'top_k': 40,
			'top_p': .8,
			'do_sample': True,
			'repetition_penalty': 1.08,
			'stop_token': '<|endoftext|>'
		}
		self.model_path: str = os.environ["Model"]
		self.model = LanguageGenerationModel("gpt2", self.model_path, use_cuda=False)
		self.head_model = GPT2LMHeadModel.from_pretrained(self.model_path)
		self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_path)

	def generate_text(self, prompt: str):
		start_time = time.time()

		output_list = self.model.generate(prompt=prompt, args=self.text_generation_parameters)

		end_time = time.time()
		duration = round(end_time - start_time, 1)

		logging.info(f'{len(output_list)} sample(s) of text generated in {duration} seconds.')

		if output_list:
			return output_list[0].replace(prompt, "")

	def generate_other_text(self, prompt: str) -> str:
		generated = self.tokenizer(f"<|startoftext|> {prompt}", return_tensors="pt")

		sample_outputs = self.head_model.generate(inputs=generated.input_ids,
										attention_mask=generated['attention_mask'],
										do_sample=True,
										top_k=40,
										max_length=1024,
										top_p=0.8,
										temperature=0.8,
										num_return_sequences=1,
										repetition_penalty=1.08)
		replies = []
		for i, sample_output in enumerate(sample_outputs):
			result = self.tokenizer.decode(sample_output, skip_special_tokens=True)
			result = result.replace(prompt, "")
			replies.append(result)
			print("{}: {}\n".format(i, result.replace(prompt, "")))

		return replies[0]