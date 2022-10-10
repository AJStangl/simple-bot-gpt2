import logging
import sys
import threading
import time

import praw
from praw import Reddit
from praw.models import Subreddit

from shared_code.processes.polling import StreamPolling


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True)
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True)
		self.create_post_thread = threading.Thread(target=self.poll_for_submission_creation, args=(), daemon=True)
		self.manager_thread = threading.Thread(target=self.manager, args=(), daemon=True)

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_submissions()

	def poll_for_submission_creation(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_content_creation()

	def manager(self):
		while True:
			logging.info("=" * 40)
			logging.info(f"|Thread ReportReporting Status:")
			logging.info(f"|{self.comment_polling_thread.name}\t|\t{self.comment_polling_thread.is_alive()}\t\t|")
			logging.info(f"|{self.submission_polling_thread.name}\t|\t{self.submission_polling_thread.is_alive()}\t\t|")
			logging.info(f"|{self.create_post_thread.name}\t|\t{self.create_post_thread.is_alive()}\t\t|")
			logging.info(f"|{self.manager_thread.name}\t|\t{self.manager_thread.is_alive()}\t\t|")
			logging.info("=" * 40 + "\n")
			time.sleep(120)

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()
		self.create_post_thread.start()
		self.manager_thread.start()

	@staticmethod
	def stop():
		sys.exit(0)
