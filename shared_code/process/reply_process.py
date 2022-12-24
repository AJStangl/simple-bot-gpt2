import gc
import json
import logging
import random
import time
from multiprocessing import Process

import praw
import torch
from praw.reddit import Comment, Submission, Subreddit

from shared_code.messaging.message_sender import MessageBroker
import re
class Helper:

	@staticmethod
	def set_global_logging_level(level=logging.ERROR, prefices=[""]):
		prefix_re = re.compile(fr'^(?:{ "|".join(prefices) })')
		for name in logging.root.manager.loggerDict:
			if re.match(prefix_re, name):
				logging.getLogger(name).setLevel(level)

class ReplyProcess:
	def __init__(self):
		self.message_broker = MessageBroker()

	def poll_for_reply(self):
		"""
		Polls the message queue for a reply to a comment. In Process Method
		:return:
		"""
		logging.info(f"Starting Poll For Reply")
		while True:
			try:
				message = self.message_broker.get_message("message-generator")
				if message:
					content = message.content
					q = json.loads(content)
					logging.debug(f"Processing Message For Reply")
					p = Process(target=self.reply_to_thing, args=(q,), daemon=True)
					p.start()
					self.message_broker.delete_message("message-generator", message)
					p.join()
					logging.debug(f"Finished Processing Queue Item")
			finally:
				time.sleep(10)

	@staticmethod
	def reply_to_thing(q: dict):
		from shared_code.text_generation.text.text_generation import ModelTextGenerator
		"""
		Replies to a comment or submission. Out of process method
		:param q:
		:return:
		"""
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s',
							level=logging.INFO)
		max_comments = 500
		try:
			name = q.get("name")
			prompt = q.get("prompt")
			thing_id = q.get("id")
			thing_type = q.get("type")
			logging.info(f"Call To Create New Reply To Comment Reply for {name}")
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
		"""
		Polls the message queue for a submission to reply to. In Process Method
		:return:
		"""
		logging.info(f"Starting Poll For Submission")
		while True:
			try:
				message = self.message_broker.get_message("submission-generator")
				if message:
					content = message.content
					q = json.loads(content)
					logging.debug(f"Processing Message For Submission")
					p = Process(target=self.create_new_submission, args=(q,), daemon=True)
					p.start()
					self.message_broker.delete_message("submission-generator", message)
					p.join()
					logging.debug(f"Finished Processing Submission Queue Item")
			finally:
				time.sleep(10)

	@staticmethod
	def create_new_submission(q):
		"""
		Creates a new submission. Out of process method
		:param q:
		:return:
		"""
		from shared_code.text_generation.text.text_generation import ModelTextGenerator
		import logging
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		Helper.set_global_logging_level()
		broker = MessageBroker()
		logging.info("Acquired Submission Lock")
		try:
			bot_name = q.get("name")
			subreddit_name = q.get("subreddit")
			post_type = q.get("type")
			logging.info(f"Call To Create New Submission for {bot_name} to {subreddit_name} with type {post_type}")

			instance = praw.Reddit(site_name=bot_name)
			generator = ModelTextGenerator(bot_name, torch.cuda.is_available())

			subreddit: Subreddit = instance.subreddit(subreddit_name)

			result: dict = generator.generate_submission(subreddit_name, post_type)

			if result.get("type") == "text":
				result = subreddit.submit(title=result.get("title"), selftext=result.get("selftext"))
				if result:
					logging.info(f"Successfully created new submission to {subreddit_name} for {bot_name}")
					return
				else:
					logging.info(f"Failed to create new submission to {subreddit_name} for {bot_name}")
					lock = broker.get_message("submission-lock")
					pop_receipt = lock.pop_receipt
					broker.delete_message("submission-lock", lock, pop_receipt)
					return

			if result.get("type") == "link":
				result = subreddit.submit(title=result.get("title"), url=result.get("url"))
				if result:
					logging.info(f"Successfully created new link submission to {subreddit_name} for {bot_name}")
					return
				else:
					logging.info(f"Failed to create new link submission to {subreddit_name} for {bot_name}")
					lock = broker.get_message("submission-lock")
					pop_receipt = lock.pop_receipt
					broker.delete_message("submission-lock", lock, pop_receipt)
					return

			if result.get("type") == "image":
				result = subreddit.submit_image(title=result.get("title"), image_path=result.get("image_path"))
				if result:
					logging.info(f"Successfully created new image submission to {subreddit_name} for {bot_name}")
					return
				else:
					logging.info(f"Failed To Create New Image Submission to {subreddit_name} for {bot_name}")
					lock = broker.get_message("submission-lock")
					pop_receipt = lock.pop_receipt
					broker.delete_message("submission-lock", lock, pop_receipt)
					return

		except Exception as e:
			logging.error(f"Failed To Create New Submission. An exception has occurred: {e}")
			lock = broker.get_message("submission-lock")
			pop_receipt = lock.pop_receipt
			broker.delete_message("submission-lock", lock, pop_receipt)
			return
		finally:
			torch.cuda.empty_cache()
			gc.collect()

	def delete_lock(self):
		"""
		Deletes the submission lock
		:return:
		"""
		logging.info(f"Deleting Submission Lock")

class SubmissionProcess:
	def __init__(self, bot_name: str):
		self.message_broker = MessageBroker()
		self.bot_name = bot_name

	def poll_for_creation(self):
		"""
		Polls the message queue for a submission to create. In Process Method
		:return:
		"""
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
			submission_lock = broker.count_message("submission-lock")

			if submission_lock == 0:
				logging.info(f"Sending message to queue for {bot} with post type: {topic_type} to sub {sub}")
				broker.put_message("submission-generator", json.dumps(message))
				broker.put_message("submission-lock", json.dumps({"lock": True}), time_to_live=60*60)
				time.sleep(5 * 1)
			else:
				logging.debug(f"Submission Lock Exists. Sleeping for 1 minutes")
				time.sleep(60 * 1)
