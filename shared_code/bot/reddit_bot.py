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
		self.self_mention_polling_thread = threading.Thread(target=self.poll_for_mentions, args=(), daemon=True)
		self.create_post_thread = threading.Thread(target=self.poll_for_submission_creation, args=(), daemon=True)
		self.management_thread = threading.Thread(target=self.management, args=(), daemon=True)

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_submissions()

	def poll_for_mentions(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_mentions()

	def poll_for_submission_creation(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_content_creation()

	def management(self):
		while True:
			time.sleep(60)



	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()
		self.self_mention_polling_thread.start()
		self.create_post_thread.start()
		self.management_thread.start()

	@staticmethod
	def stop():
		sys.exit(0)
