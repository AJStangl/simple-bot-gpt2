import logging
import multiprocessing
import sys
import threading
import time

import praw
import torch
from praw import Reddit
from praw.models import Subreddit
from praw.reddit import Comment, Submission

from shared_code.processes.polling import StreamPolling
from multiprocessing import Process, Queue

from shared_code.text_generation.text_generation import ModelTextGenerator


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)
		# Threads
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True, name="Thread-GC")
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True, name="Thread-GS")
		self.create_post_thread = threading.Thread(target=self.poll_for_submission_creation, args=(), daemon=True, name="Thread-PS")
		self.queue_thread = threading.Thread(target=self.poll_for_queue, args=(),  daemon=True, name="Thread-RQ")
		self.manager_thread = threading.Thread(target=self.manager, args=(), daemon=True, name="Thread-MM")
		self.queue = Queue()

	@staticmethod
	def do_thing(q):
		print(f":: Starting New Process Language Generation Process")
		name = q.get("name")
		prompt = q.get("prompt")
		thing_id = q.get("id")
		thing_type = q.get("type")
		if thing_type == "comment":
			text, raw_text = ModelTextGenerator(name, torch.cuda.is_available()).generate_text(prompt)
			comment: Comment = praw.Reddit(site_name=name).comment(id=thing_id)
			comment.reply(body=text)
			print(f":: Replied To Comment")
		if thing_type == "submission":
			text, raw_text = ModelTextGenerator(name, torch.cuda.is_available()).generate_text(prompt)
			submission: Submission = praw.Reddit(site_name=name).submission(id=thing_id)
			submission.reply(body=text)
			print(f":: Replied To Submission")
		return

	def poll_for_queue(self):
		while True:
			logging.info(f"Number Of Items In Queue: {self.queue.qsize()}")
			queue_item = self.queue.get()
			if queue_item:
				logging.info(f"Object Received From Queue {queue_item}")
				proc = multiprocessing.Process(target=self.do_thing, args=(queue_item,))
				proc.start()
				proc.join()

			time.sleep(10)

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit, self.queue).poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit, self.queue).poll_for_submissions()

	def poll_for_submission_creation(self):
		StreamPolling(self.reddit, self.subreddit, self.queue).poll_for_content_creation()

	def manager(self):
		while True:
			logging.info("=" * 40)
			logging.info(f"|Thread Reporting Status:")
			logging.info(f"|{self.comment_polling_thread.name}\t|\t{self.comment_polling_thread.is_alive()}\t\t|")
			logging.info(f"|{self.submission_polling_thread.name}\t|\t{self.submission_polling_thread.is_alive()}\t\t|")
			logging.info(f"|{self.create_post_thread.name}\t|\t{self.create_post_thread.is_alive()}\t\t|")
			logging.info(f"|{self.queue_thread.name}\t|\t{self.queue_thread.is_alive()}\t\t|")
			logging.info(f"|{self.manager_thread.name}\t|\t{self.manager_thread.is_alive()}\t\t|")
			logging.info("=" * 40 + "\n")
			time.sleep(120)

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()
		self.create_post_thread.start()
		self.queue_thread.start()
		self.manager_thread.start()

	def stop(self):
		sys.exit(0)
