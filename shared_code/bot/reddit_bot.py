import sys
import threading

import praw
from praw import Reddit
from praw.models import Subreddit

from shared_code.processes.polling import StreamPolling


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True) # Separate thread process
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True) # Separate thread process

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit).poll_for_submissions()

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()

	@staticmethod
	def stop():
		sys.exit(0)

