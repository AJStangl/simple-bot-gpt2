import logging
import time

from shared_code.bot.reddit_bot import RedditBot
from shared_code.bot.reddit_bot_processor import RedditBotProcessor, RedditSubmissionProcessor
from shared_code.utility.global_logging_filter import LoggingExtension

LoggingExtension.set_global_logging_level(logging.FATAL)
logging_format = LoggingExtension.get_logging_format()
class BotRunner:

	@staticmethod
	def run_bots(bot_names: [str], sub_reddit: str):
		logging.basicConfig(format=logging_format,
							level=logging.INFO)
		bots = []
		submission_procs = []
		for bot_name in bot_names:
			bot = RedditBot(bot_name, sub_reddit)
			bot.name = bot_name
			bot.daemon = True
			bot.run()
			bots.append(bot)
			time.sleep(1)


		submission_process = RedditSubmissionProcessor()
		submission_process.daemon = True
		submission_process.run()
		submission_procs.append(submission_process)

		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), bots)
			map(lambda x: x.stop(), submission_procs)
			exit(0)

	@staticmethod
	def run_process(thread_count: int = 1):
		logging.basicConfig(format=logging_format, level=logging.INFO)
		procs = []
		for i in range(thread_count):
			process = RedditBotProcessor(bot_name=f"Reply-Thread-{i}")
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
		logging.basicConfig(format=logging_format, level=logging.INFO)
		bots = []
		submission_procs = []
		reply_procs = []

		for i in range(thread_count):
			reply_process = RedditBotProcessor(bot_name=f"Reply-Thread-{i}")
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

		submission_process = RedditSubmissionProcessor()
		submission_process.daemon = True
		submission_process.run()
		submission_procs.append(submission_process)

		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt:
			logging.info('Shutdown')
			map(lambda x: x.stop(), reply_procs)
			map(lambda x: x.stop(), submission_procs)
			map(lambda x: x.stop(), bots)
			exit(0)

