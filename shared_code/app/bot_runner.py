import logging
import time
from shared_code.bot.reddit_bot import RedditBot


class BotRunner:

	@staticmethod
	def run_multi_bot(bot_names: [str], sub_reddit: str):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		bots = []
		for bot_name in bot_names:
			bot = RedditBot(bot_name, sub_reddit)
			bot.name = bot_name
			bot.daemon = True
			bot.run()
			bots.append(bot)
			time.sleep(10)
		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), bots)
			exit(0)
