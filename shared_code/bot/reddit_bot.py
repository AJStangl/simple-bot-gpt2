import logging
import sys
import threading
import time
from multiprocessing import Process, Queue


import torch
import pbfaw as praw
from pbfaw import Reddit
from pbfaw.models import Subreddit
from pbfaw.reddit import Comment, Submission
from shared_code.handlers.polling_handler import StreamPolling
from shared_code.handlers.queue_handler import QueueHandler
from shared_code.text_generation.text.text_generation import ModelTextGenerator


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name, ratelimit_seconds=600)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)

		# Threads
		self.poll_for_comments_and_submissions_thread = threading.Thread(target=self.poll_for_comments_and_submissions, args=(), daemon=True, name="Thread-ALL")
		self.poll_for_reply_queue_thread = threading.Thread(target=self.poll_for_reply_queue, args=(), daemon=True, name="Thread-RQ")
		self.poll_for_submission_queue_thread = threading.Thread(target=self.poll_for_submission_queue, args=(), daemon=True, name="Thread-SG")

		# Queues
		self.comment_queue = Queue()

	def poll_for_reply_queue(self):
		"""Thread for independent Queue Handler For Generation of Replies"""
		QueueHandler(self.comment_queue, self.reddit, self.subreddit).poll_for_reply()

	def poll_for_submission_queue(self):
		"""Thread for independent Queue Handler For Generation of Replies"""
		QueueHandler(self.comment_queue,  self.reddit, self.subreddit).poll_for_submission_generation()

	def poll_for_comments_and_submissions(self):
		"""Thread for independent Polling Handler For Comments and Submissions"""
		StreamPolling(self.reddit, self.subreddit, self.comment_queue).poll_for_all()

	def run(self):
		"""Starts the bot - Invoked from run_bot.py"""
		self.poll_for_comments_and_submissions_thread.start()
		self.poll_for_submission_queue_thread.start()
		self.poll_for_reply_queue_thread.start()

	# noinspection PyMethodMayBeStatic
	def stop(self):
		sys.exit(0)
