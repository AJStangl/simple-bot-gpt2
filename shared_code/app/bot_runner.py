import logging
import time

from shared_code.bot.reddit_bot import RedditBot
from shared_code.bot.reddit_bot_processor import RedditBotProcessor, RedditSubmissionProcessor


class BotRunner:

	@staticmethod
	def run_bots(bot_names: [str], sub_reddit: str):
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
	def run_all(bot_names: str, sub_reddit: str, thread_count: int = 1):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		bots = []
		submission_procs = []
		reply_procs = []

		for i in range(thread_count):
			reply_process = RedditBotProcessor(f"Reply-Thread-{i}")
			reply_process.daemon = True
			reply_process.run()
			reply_procs.append(reply_process)
			time.sleep(1)

		for bot_name in bot_names.split(','):
			bot = RedditBot(bot_name, sub_reddit)
			bot.name = bot_name
			bot.daemon = True
			bot.run()
			bots.append(bot)
			time.sleep(1)

		for bot_name in bot_names.split(','):
			submission_process = RedditSubmissionProcessor(bot_name)
			submission_process.name = bot_name
			submission_process.daemon = True
			submission_process.run()
			submission_procs.append(submission_process)
			time.sleep(10)

		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), reply_procs)
			map(lambda x: x.stop(), submission_procs)
			map(lambda x: x.stop(), bots)
			exit(0)

