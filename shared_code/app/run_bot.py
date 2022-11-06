import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
from shared_code.bot.reddit_bot import RedditBot


class BotRunner:

	@staticmethod
	def run_bot(bot_name: str, sub_reddit: str):
		logging = logging.getLogger(__name__)
		logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{bot_name}|%(message)s', level=logging.INFO)
		bot = RedditBot(bot_name, sub_reddit)
		bot.run()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			bot.stop()

	@staticmethod
	def run_multi_bot(bot_names: str, sub_reddit: str):
		for bot_name in bot_names.split(","):
			bot = RedditBot(bot_name, sub_reddit)
			bot.run()
		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			bot.stop()