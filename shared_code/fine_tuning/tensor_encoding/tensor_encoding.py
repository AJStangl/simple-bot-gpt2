from logging import getLogger
from typing import List
from transformers.tokenization_utils_base import TextInput

logger = getLogger("TokenizerAdapter")


class TokenizerAdapter(object):
	"""
	Provides an interface to tokenization related activities. Intended to be extended on from this type.
	"""

	# Private constant for maximum acceptable length of GPT-2 models. Perhaps this requires further abstraction
	MAX_TOKEN_LIMIT: int = 1024

	def __init__(self, tokenizer):
		self.__tokenizer = tokenizer

	def tokenize(self, text: TextInput, **kwargs) -> List[str]:
		"""Wrapper for direct call to provider tokenizer tokenize method"""
		return self.__tokenizer.tokenize(text, **kwargs)

	def token_length_appropriate(self, prompt) -> bool:
		"""
		Ensures that the total number of encoded tokens is within acceptable limits.
		:param prompt: UTF-8 Text that is assumed to have been processed.
		:return: True if acceptable.
		"""
		tokens = self.tokenize(prompt)
		if len(tokens) > self.MAX_TOKEN_LIMIT:
			logger.debug(f":: Tokens for model input is > {1024}. Skipping input")
			return False
		else:
			return True
