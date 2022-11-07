import logging
import random
import time
from multiprocessing import Process, Queue
import gc

import torch
import praw
from praw.reddit import Comment, Submission, Reddit, Subreddit

from shared_code.text_generation.text.text_generation import ModelTextGenerator


class QueueHandler(object):
	def __init__(self, comment_queue: Queue, reddit: Reddit, subreddit):
		self.queue: Queue = comment_queue
		self.reddit: Reddit = reddit
		self.subreddit = subreddit
		self.time_since_post = random.randint(300, 600)

	@staticmethod
	def reply_to_thing(q):
		import logging
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.info(f"::Call To Create New Reply To Comment")
		generator = None
		instance = None
		try:
			logging.info(f":: Starting New Process Language Generation Process")
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
					logging.info(f":: Successfully replied to comment {thing_id}")
					logging.info(f":: Finished Language Generation Process...Cleaning up")
					return
				else:
					logging.info(f":: Failed to reply to comment {thing_id}")
					return

			if thing_type == "submission":
				text, raw_text = generator.generate_text(prompt)
				submission: Submission = instance.submission(id=thing_id)
				reply = submission.reply(body=text)
				if reply:
					logging.info(f":: Successfully replied to submission {thing_id}")
					logging.info(f":: Finished Language Generation Process...Cleaning up")
					return
				else:
					logging.info(f":: Failed To Reply To Submission")
					return
		except Exception as e:
			logging.info(f":: Exception Occurred: {e} attempting to reply")
			return
		finally:
			del generator, instance
			torch.cuda.empty_cache()
			gc.collect()

	@staticmethod
	def create_new_submission(q):
		import logging
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.info(f"::Call To Create New Submission")
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
					logging.info(f":: Successfully created new submission to {subreddit_name} for {bot_name}")

			if result.get("type") == "link":
				result = subreddit.submit(title=result.get("title"), url=result.get("url"))
				if result:
					logging.info(f":: Successfully created new link submission to {subreddit_name} for {bot_name}")

		except Exception as e:
			print(f":: Failed To Create New Submission: {e}")
			return
		finally:
			del generator, instance
			torch.cuda.empty_cache()
			gc.collect()

	def poll_for_reply(self):
		logging.info(f"Starting poll_for_reply")
		while True:
			try:
				logging.debug(f"Number Of Items In Queue: {self.queue.qsize()}, processing next item")
				q = self.queue.get()
				if q:
					p = Process(target=self.reply_to_thing, args=(q,), daemon=True)
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
					for m in message:
						p = Process(target=self.create_new_submission, args=(m,), daemon=True)
						p.start()
						p.join()
						if p.exitcode == 0:
							logging.info(f"::p.exitcode: {p.exitcode}")
							self.time_since_post = 3600
					continue
				else:
					continue
			finally:
				self.time_since_post -= 30
				time.sleep(30)

	def create_submission_message(self, post_type):
		subs = self.subreddit.display_name.split("+")
		for sub in subs:
			logging.info(f"Creating Submission Message For {post_type}")
			foo = {
				"name": self.reddit.user.me().name,
				"subreddit": sub,
				"type": post_type
			}
			yield foo

