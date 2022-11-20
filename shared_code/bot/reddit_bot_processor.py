import logging
import sys
import threading

from shared_code.handlers.reply_process import ReplyProcess


class RedditBotProcessor(threading.Thread):
	def __init__(self, bot_name: str):
		super().__init__(name=bot_name, daemon=True)
		self.poll_for_reply_queue_thread = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name=bot_name)
		self.poll_for_submission_queue_thread = threading.Thread(target=self.poll_for_submission_queue, args=(), daemon=True, name=bot_name)

	@staticmethod
	def poll_for_reply_queue():
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		ReplyProcess().poll_for_reply()

	@staticmethod
	def poll_for_submission_queue():
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
		ReplyProcess().poll_for_submission()

	def run(self):
		self.poll_for_reply_queue_thread.start()
		self.poll_for_submission_queue_thread.start()

	def stop(self):
		sys.exit(0)
