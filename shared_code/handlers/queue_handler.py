import logging
import random
import time
from multiprocessing import Process, Queue

import pbfaw as praw
import torch
from pbfaw.reddit import Comment, Submission, Reddit, Subreddit

from shared_code.text_generation.text.text_generation import ModelTextGenerator


class QueueHandler:
	def __init__(self, comment_queue: Queue, reddit: Reddit, subreddit: Subreddit):
		self.queue: Queue = comment_queue
		self.reddit: Reddit = reddit
		self.subreddit: Subreddit = subreddit
		self.time_since_post = 0

	@staticmethod
	def reply_to_thing(q):
		generator = None
		instance = None
		try:
			print(f":: Starting New Process Language Generation Process")
			name = q.get("name")
			prompt = q.get("prompt")
			thing_id = q.get("id")
			thing_type = q.get("type")
			generator = ModelTextGenerator(name, torch.cuda.is_available())
			instance = praw.Reddit(site_name=name, ratelimit_seconds=600)
			if thing_type == "comment":
				text, raw_text = generator.generate_text(prompt)
				comment: Comment = instance.comment(id=thing_id)
				reply = comment.reply(body=text)
				if reply:
					print(f":: Successfully replied to comment {thing_id}")
					print(f":: Finished Language Generation Process...Cleaning up")
					return
				else:
					raise Exception(f":: Failed to reply to comment {thing_id}")

			if thing_type == "submission":
				text, raw_text = generator.generate_text(prompt)
				submission: Submission = instance.submission(id=thing_id)
				reply = submission.reply(body=text)
				if reply:
					print(f":: Successfully replied to submission {thing_id}")
					print(f":: Finished Language Generation Process...Cleaning up")
					return
				else:
					raise Exception(f":: Failed To Reply To Submission")
		finally:
			del generator, instance

	@staticmethod
	def create_new_submission(q):
		instance = None
		generator = None
		try:
			print(f":: Call To Create New Submission")
			bot_name = q.get("name")
			subreddit_name = q.get("subreddit")
			post_type = q.get("type")
			instance = praw.Reddit(site_name=bot_name, ratelimit_seconds=600)
			generator = ModelTextGenerator(bot_name, torch.cuda.is_available())

			subreddit: Subreddit = instance.subreddit(subreddit_name)
			result: dict = generator.generate_submission(subreddit_name, post_type)

			if result.get("type") == "text":
				result = subreddit.submit(title=result.get("title"), selftext=result.get("selftext"))
				if result:
					print(f":: Successfully created new submission to {subreddit_name} for {bot_name}")

			if result.get("type") == "link":
				result = subreddit.submit(title=result.get("title"), url=result.get("url"))
				if result:
					print(f":: Successfully created new link submission to {subreddit_name} for {bot_name}")
		finally:
			del generator, instance

	def poll_for_reply(self):
		logging.info(f"Starting poll_for_reply")
		while True:
			try:
				logging.debug(f"Number Of Items In Queue: {self.queue.qsize()}, processing next item")
				q = self.queue.get()
				if q:
					p = Process(target=self.reply_to_thing, args=(q,))
					p.start()
					p.join()
					logging.info(f"Finished Processing Queue Item")
			finally:
				time.sleep(10)

	def poll_for_submission_generation(self):
		logging.info(f"Starting poll_for_submission_generation")
		post_types = random.choice(["text", "link"])
		while True:
			try:
				if self.time_since_post <= 0:
					message = self.create_submission_message(post_type=post_types)
					p = Process(target=self.create_new_submission, args=(message,))
					p.start()
					p.join()
					self.time_since_post = 3600
					continue
				else:
					continue
			finally:
				self.time_since_post -= 10
				time.sleep(10)

	def create_submission_message(self, post_type):
		logging.info(f"Creating Submission Message For {post_type}")
		return {
			"name": self.reddit.user.me().name,
			"subreddit": self.subreddit.display_name,
			"type": post_type
		}
