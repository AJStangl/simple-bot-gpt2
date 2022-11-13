import sys
import threading
from multiprocessing import Queue

import praw
from praw import Reddit
from praw.models import Subreddit
from shared_code.handlers.polling_handler import StreamPolling
from shared_code.handlers.queue_handler import QueueHandler
import sys
import threading
from multiprocessing import Queue

import praw
from praw import Reddit
from praw.models import Subreddit

from shared_code.handlers.polling_handler import StreamPolling
from shared_code.handlers.queue_handler import QueueHandler


class RedditBot(threading.Thread):
	def __init__(self, bot_name: str, subreddit):
		super().__init__(name=bot_name, daemon=True)
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)

		# Threads - Polling
		self.poll_for_submissions_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True, name=bot_name)
		self.poll_for_comments_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True, name=bot_name)

		# Threads - Queue
		# self.poll_for_submission_queue_thread = threading.Thread(target=self.poll_for_submission_queue, args=(), daemon=True, name=bot_name)

		# Threads - Distributed Queue
		# self.poll_for_reply_queue_thread_1 = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name=bot_name)
		# self.poll_for_reply_queue_thread_2 = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name=bot_name)
		# self.poll_for_reply_queue_thread_3 = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name=bot_name)

		# Queues
		self.comment_queue = Queue()

	def poll_for_reply_queue(self):
		"""Thread for independent Queue Handler For Generation of Replies"""
		QueueHandler(self.comment_queue, self.reddit, self.subreddit).poll_for_reply()

	def poll_for_submission_queue(self):
		"""Thread for independent Queue Handler For Generation of Replies"""
		QueueHandler(self.comment_queue, self.reddit, self.subreddit).poll_for_submission_generation()

	def poll_for_comments(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		StreamPolling(self.reddit, self.subreddit, self.comment_queue).poll_for_comments()

	def poll_for_submissions(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		StreamPolling(self.reddit, self.subreddit, self.comment_queue).poll_for_submissions()

	def run(self):
		"""Starts the bot - Invoked from run_bot.py"""
		self.poll_for_submissions_thread.start()
		self.poll_for_comments_thread.start()
		# self.poll_for_submission_queue_thread.start()
		# self.poll_for_reply_queue_thread_1.start()
		# self.poll_for_reply_queue_thread_2.start()
		# self.poll_for_reply_queue_thread_3.start()

	# noinspection PyMethodMayBeStatic
	def stop(self):
		sys.exit(0)
