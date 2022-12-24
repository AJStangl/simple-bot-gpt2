import gc
import json
import logging
import os
import time
from multiprocessing import Process

import praw
import torch
import random
from praw.reddit import Comment, Submission, Subreddit

from shared_code.messaging.message_sender import MessageBroker
from shared_code.text_generation.text.text_generation import ModelTextGenerator


class ReplyProcess:
	def __init__(self):
		self.message_broker = MessageBroker()

	def poll_for_reply(self):
		logging.info(f"Starting Poll For Reply")
		while True:
			try:
				message = self.message_broker.get_message("message-generator")
				if message:
					content = message.content
					q = json.loads(content)
					logging.info(f"Processing Message For Reply")
					p = Process(target=self.reply_to_thing, args=(q,), daemon=True)
					p.start()
					self.message_broker.delete_message("message-generator", message)
					p.join()
					logging.info(f"Finished Processing Queue Item")
			finally:
				time.sleep(10)

	@staticmethod
	def reply_to_thing(q: dict):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s',
							level=logging.INFO)
		logging.info(f"Call To Create New Reply To Comment Reply")
		max_comments = 500
		try:
			name = q.get("name")
			prompt = q.get("prompt")
			thing_id = q.get("id")
			thing_type = q.get("type")
			generator = ModelTextGenerator(name, torch.cuda.is_available())
			instance = praw.Reddit(site_name=name)
			if thing_type == "comment":
				comment: Comment = instance.comment(id=thing_id)
				submission: Submission = comment.submission
				if submission.locked:
					logging.info(f"Submission is locked, skipping")
					return
				if submission.num_comments > max_comments:
					logging.info(f"Comment Has More Than {max_comments} Comments, Skipping")
					return

				text, raw_text = generator.generate_text(prompt)
				reply = comment.reply(body=text)
				if reply:
					logging.info(f"Successfully replied to comment {thing_id}")
					return
				else:
					logging.info(f"Failed to reply to comment {thing_id}")
					return

			if thing_type == "submission":
				submission: Submission = instance.submission(id=thing_id)
				if submission.locked:
					logging.info(f"Submission is locked, skipping")
					return
				text, raw_text = generator.generate_text(prompt)
				reply = submission.reply(body=text)
				if reply:
					logging.info(f"Successfully replied to submission {thing_id}")
					return
				else:
					logging.info(f"Failed To Reply To Submission")
					return
		except Exception as e:
			logging.info(f"Exception Occurred: {e} attempting to reply")
			return
		finally:
			torch.cuda.empty_cache()
			gc.collect()

	def poll_for_submission(self):
		logging.info(f"Starting Poll For Submission")
		while True:
			try:
				message = self.message_broker.get_message("submission-generator")
				if message:
					content = message.content
					q = json.loads(content)
					logging.info(f"Processing Message For Submission")
					p = Process(target=self.create_new_submission, args=(q,), daemon=True)
					p.start()
					self.message_broker.delete_message("submission-generator", message)
					p.join()
					logging.info(f"Finished Processing Submission Queue Item")
			finally:
				time.sleep(10)

	@staticmethod
	def create_new_submission(q):
		import logging
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s',
							level=logging.INFO)
		logging.info(f"Call To Create New Submission")
		try:
			bot_name = q.get("name")
			subreddit_name = q.get("subreddit")
			post_type = q.get("type")
			instance = praw.Reddit(site_name=bot_name)
			generator = ModelTextGenerator(bot_name, torch.cuda.is_available())

			subreddit: Subreddit = instance.subreddit(subreddit_name)

			result: dict = generator.generate_submission(subreddit_name, post_type)

			if result.get("type") == "text":
				result = subreddit.submit(title=result.get("title"), selftext=result.get("selftext"),
										  flair_id=os.environ["subreddit_flair"])
				if result:
					logging.info(f"Successfully created new submission to {subreddit_name} for {bot_name}")

			if result.get("type") == "link":
				result = subreddit.submit(title=result.get("title"), url=result.get("url"),
										  flair_id=os.environ["subreddit_flair"])
				if result:
					logging.info(f"Successfully created new link submission to {subreddit_name} for {bot_name}")

			if result.get("type") == "image":
				result = subreddit.submit_image(title=result.get("title"), image_path=result.get("image_path"),
												flair_id=os.environ["subreddit_flair"])
				if result:
					logging.info(f"Successfully created new image submission to {subreddit_name} for {bot_name}")

		except Exception as e:
			logging.error(f"Failed To Create New Submission: {e}")
			return
		finally:
			torch.cuda.empty_cache()
			gc.collect()


class SubmissionProcess:
	def __init__(self, bot_name: str):
		self.message_broker = MessageBroker()
		self.bot_name = bot_name

	def poll_for_creation(self):
		subs = os.environ["SubToPost"].split(",")
		# 5 in 10 chance image, 3 in one chance text, 1 10 chance text
		post_type = ["image", "image", "image", "image", "image", "text", "text", "text", "text", "link"]
		subs = ["CoopAndPabloPlayHouse"]
		while True:
			sub = random.choice(subs)
			bot = self.bot_name
			topic_type = random.choice(post_type)

			message = {
				"name": bot,
				"subreddit": sub,
				"type": topic_type,
			}
			broker = MessageBroker()
			count = broker.count_message("submission-generator")
			while count > 1:
				time.sleep(30)
			print(f"Sending message to queue for {bot} with post type: {topic_type} to sub {sub}")
			broker.put_message("submission-generator", json.dumps(message))
			if topic_type == "image":
				time.sleep(60 * 60 * random.randint(1, 3))
			if topic_type == "text":
				time.sleep(60 * 60 * random.randint(1, 3))
			if topic_type == "link":
				time.sleep(60 * 60 * random.randint(1, 3))
			else:
				time.sleep(60 * 60 * random.randint(1, 3))
