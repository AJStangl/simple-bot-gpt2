import logging
import sys
import threading
from multiprocessing import Process, Queue

import praw
import torch
from praw import Reddit
from praw.models import Subreddit
from praw.reddit import Comment, Submission
from shared_code.handlers.polling_handler import StreamPolling

from shared_code.text_generation.text.text_generation import ModelTextGenerator


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(bot_name, reddit_url='https://botforum.net', oauth_url='https://oauth.botforum.net', submission_kind='t7', message_kind='t8', timeout=64);
		self.subreddit: Subreddit = self.reddit.subreddit(subreddit)
		# Threads
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True, name="Thread-GC")
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True, name="Thread-GS")
		# self.create_post_thread = threading.Thread(target=self.poll_for_submission_creation, args=(), daemon=True, name="Thread-PS")
		self.queue_thread = threading.Thread(target=self.poll_for_queue, args=(),  daemon=True, name="Thread-RQ")
		self.queue = Queue()

	@staticmethod
	def do_thing(q):
		print(f":: Starting New Process Language Generation Process")
		name = q.get("name")
		prompt = q.get("prompt")
		thing_id = q.get("id")
		thing_type = q.get("type")
		generator = ModelTextGenerator(name, torch.cuda.is_available())
		instance = praw.Reddit(site_name=name)
		if thing_type == "comment":
			text, raw_text = generator.generate_text(prompt)
			comment: Comment = instance.comment(id=thing_id)
			comment.reply(body=text)
			print(f":: Replied To Comment")
		if thing_type == "submission":
			text, raw_text = generator.generate_text(prompt)
			submission: Submission = instance.submission(id=thing_id)
			submission.reply(body=text)
			print(f":: Replied To Submission")

		print(f":: Finished Language Generation Process...Cleaning up")
		del generator, instance
		return None

	def poll_for_queue(self):
		while True:
			while self.queue.qsize() > 0:
				logging.info(f"Number Of Items In Queue: {self.queue.qsize()}")
				logging.info(f":: Processing Queue Item")
				q = self.queue.get(block=True)
				p = Process(target=self.do_thing, args=(q,))
				p.start()
				p.join()
				logging.info(f":: Finished Processing Queue Item")
				continue

	def poll_for_comments(self):
		StreamPolling(self.reddit, self.subreddit, self.queue)\
			.poll_for_comments()

	def poll_for_submissions(self):
		StreamPolling(self.reddit, self.subreddit, self.queue)\
			.poll_for_submissions()

	def poll_for_submission_creation(self):
		StreamPolling(self.reddit, self.subreddit, self.queue)\
			.poll_for_content_creation()

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()
		self.queue_thread.start()
		# self.create_post_thread.start()

	# noinspection PyMethodMayBeStatic
	def stop(self):
		sys.exit(0)
