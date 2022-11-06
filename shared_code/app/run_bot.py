import logging
import time

from shared_code.bot.reddit_bot import RedditBot


class BotRunner:

	@staticmethod
	def run_bot(bot_name: str, sub_reddit: str):
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
	def _run_bot(bot_name: str, sub_reddit: str):
		logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{bot_name}|%(message)s', level=logging.DEBUG)
		bot = RedditBot(bot_name, sub_reddit)
		bot.run()

	@staticmethod
	def run_multi_bot(bot_names: str, sub_reddit: str):
		from threading import Thread
		bots = bot_names.split(",")
		for bot in bots:
			t = Thread(target=BotRunner._run_bot, args=(bot, sub_reddit,))
			t.start()
			time.sleep(10)
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			[t.join() for t in tasks]

