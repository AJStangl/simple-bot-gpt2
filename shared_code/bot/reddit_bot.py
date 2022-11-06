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
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True, name="Thread-GC")
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True, name="Thread-GS")
		self.queue_thread = threading.Thread(target=self.poll_for_reply, args=(), daemon=True, name="Thread-RQ")


		# Queues
		self.queue = Queue()

	@staticmethod
	def reply_to_thing(q):
		print(f":: Starting New Process Language Generation Process")
		name = q.get("name")
		prompt = q.get("prompt")
		thing_id = q.get("id")
		thing_type = q.get("type")
		generator = ModelTextGenerator(name, torch.cuda.is_available())
		instance = praw.Reddit(site_name=name, ratelimit_seconds=300)
		if thing_type == "comment":
			text, raw_text = generator.generate_text(prompt)
			comment: Comment = instance.comment(id=thing_id)
			reply = comment.reply(body=text)
			if reply:
				print(f":: Successfully replied to comment {thing_id}")
				print(f":: Finished Language Generation Process...Cleaning up")
				del generator, instance
				return None
			else:
				raise Exception(f":: Failed to reply to comment {thing_id}")

		if thing_type == "submission":
			text, raw_text = generator.generate_text(prompt)
			submission: Submission = instance.submission(id=thing_id)
			reply = submission.reply(body=text)
			if reply:
				print(f":: Replied To Submission")
				print(f":: Finished Language Generation Process...Cleaning up")
				del generator, instance
				return None
			else:
				raise Exception(f":: Failed To Reply To Submission")

	def poll_for_reply(self):
		QueueHandler(self.queue)\
			.poll_for_reply()

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit, self.queue)\
			.poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit, self.queue)\
			.poll_for_submissions()

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()
		self.queue_thread.start()

	# noinspection PyMethodMayBeStatic
	def stop(self):
		sys.exit(0)
