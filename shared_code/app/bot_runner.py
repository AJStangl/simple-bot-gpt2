import logging
import time

from shared_code.bot.reddit_bot import RedditBot
from shared_code.bot.reddit_bot_processor import RedditBotProcessor


class BotRunner:

	@staticmethod
	def run_multi_bot(bot_names: [str], sub_reddit: str):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s',
							level=logging.INFO)
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

	@staticmethod
	def run_process(thread_count: int = 1):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		procs = []
		for i in range(thread_count):
			process = RedditBotProcessor(f"Reply-Thread-{i}")
			process.daemon = True
			process.run()
			procs.append(process)
			time.sleep(10)
		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), procs)
			exit(0)

	@staticmethod
	def run_all(bot_names: [str], sub_reddit: str, thread_count: int = 1):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		bots = []
		procs = []

		for i in range(thread_count):
			process = RedditBotProcessor(f"Reply-Thread-{i}")
			process.daemon = True
			process.run()
			procs.append(process)
			time.sleep(1)

		for bot_name in bot_names.split(','):
			bot = RedditBot(bot_name, sub_reddit)
			bot.name = bot_name
			bot.daemon = True
			bot.run()
			bots.append(bot)
			time.sleep(1)
		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), procs)
			map(lambda x: x.stop(), bots)
			exit(0)

