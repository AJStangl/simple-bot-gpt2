import sys
import threading

import praw
from praw import Reddit
from praw.models import Subreddit

from shared_code.handlers.polling_handler import StreamPolling
from shared_code.handlers.submission_queue_sender import SubmissionCreationHandler


class RedditBot(threading.Thread):
	def __init__(self, bot_name: str, subreddit):
		super().__init__(name=bot_name, daemon=True)
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)

		# Threads - Polling
		self.poll_for_submissions_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True, name=bot_name)
		self.poll_for_comments_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True, name=bot_name)
		self.poll_for_new_submission_thread = threading.Thread(target=self.poll_for_new_submission, args=(), daemon=True, name=bot_name)

	def poll_for_comments(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		StreamPolling(self.reddit, self.subreddit).poll_for_comments()

	def poll_for_submissions(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		StreamPolling(self.reddit, self.subreddit).poll_for_submissions()

	def poll_for_new_submission(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		SubmissionCreationHandler(self.reddit, self.subreddit).poll_for_submission_generation()

	def run(self):
		"""Starts the bot - Invoked from run_bot.py"""
		self.poll_for_submissions_thread.start()
		self.poll_for_comments_thread.start()
		self.poll_for_new_submission_thread.start()

	# noinspection PyMethodMayBeStatic
	def stop(self):
		sys.exit(0)
