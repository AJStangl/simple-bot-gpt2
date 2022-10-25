import logging
import time

from shared_code.bot.reddit_bot import RedditBot


class BotRunner:

	@staticmethod
	def run_bot(bot_name: str, sub_reddit: str):
		logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{bot_name}|%(message)s', level=logging.DEBUG)
		bot = RedditBot(bot_name, sub_reddit)
		bot.run()
		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			bot.stop()
