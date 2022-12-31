import logging
import sys
import threading

from shared_code.process.reply_process import ReplyProcess
from shared_code.utility.global_logging_filter import LoggingExtension

LoggingExtension.set_global_logging_level(logging.FATAL)
logging_format = LoggingExtension.get_logging_format()

class RedditBotProcessor(threading.Thread):
	def __init__(self, bot_name: str):
		super().__init__(name=bot_name, daemon=True)
		self.poll_for_reply_queue_thread = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name=bot_name)
		self.poll_for_submission_queue_thread = threading.Thread(target=self.poll_for_submission_queue, args=(), daemon=True, name=bot_name)

	@staticmethod
	def poll_for_reply_queue():
		logging.basicConfig(format=logging_format, level=logging.INFO)
		ReplyProcess().poll_for_reply()

	@staticmethod
	def poll_for_submission_queue():
		logging.basicConfig(format=logging_format, level=logging.INFO)
		ReplyProcess().poll_for_submission()

	def run(self):
		self.poll_for_reply_queue_thread.start()
		self.poll_for_submission_queue_thread.start()

	def stop(self):
		sys.exit(0)


class RedditSubmissionProcessor(threading.Thread):
	def __init__(self):
		super().__init__(daemon=True)
		self.poll_for_submission_creation_thread = threading.Thread(target=self.poll_for_submission_creation, args=(), daemon=True)

	def poll_for_submission_creation(self):
		logging.basicConfig(format=logging_format, level=logging.INFO)
		ReplyProcess().poll_for_creation()

	def run(self):
		self.poll_for_submission_creation_thread.start()

	def stop(self):
		sys.exit(0)