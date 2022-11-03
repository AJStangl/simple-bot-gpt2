import datetime
import logging
import os
import random
import time
from datetime import timezone
from multiprocessing.queues import Queue

from praw import Reddit
from praw.models import Redditor, Submission, Comment, Subreddit, ListingGenerator
from praw.models.reddit.base import RedditBase

from shared_code.handlers.tagging_handler import TaggingHandler
from shared_code.tagging.reddit_data import RedditData
from shared_code.text_generation.text_generation import ModelTextGenerator


class StreamPolling(object):
	def __init__(self, reddit: Reddit, subreddit: Subreddit, queue: Queue):
		self.reddit: Reddit = reddit
		self.subreddit = subreddit
		self.me: Redditor = self.reddit.user.me()
		self.prompt_handler: TaggingHandler = TaggingHandler(self.reddit)
		self.reply_threshold = int(os.environ["ReplyThreshold"])
		self.tigger_words: [str] = [item.lower() for item in os.environ["TriggerWords"].split(",")]
		self.queue = queue

	def poll_for_comments(self):
		logging.info(f"Starting Poll For {self.me} and monitoring {self.subreddit} Comments")
		while True:
			try:
				for comment in self.subreddit.stream.comments(pause_after=0, skip_existing=True):
					comment: Comment = comment
					if comment is None:
						logging.debug("No New Comments, continuing...")
						time.sleep(5)
						continue

					logging.debug(f"Comment {comment} found")
					if comment.author.name == self.me.name:
						time.sleep(5)
						continue

					if self._should_reply(comment):
						logging.info(f"Processing Response For Comment: {comment}")
						reddit_data: RedditData = self.prompt_handler.handle_comment(comment)
						prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
						q = {'id': comment.id, 'name': self.me.name, 'prompt': prompt, 'type': 'comment'}
						self.queue.put(q)
						# self.do_thing(q)
						time.sleep(5)

			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				time.sleep(5)
				continue

	def poll_for_submissions(self):
		logging.info(f"Starting Poll For {self.me} and monitoring {self.subreddit} Submissions")
		while True:
			try:
				for submission in self.subreddit.stream.submissions(pause_after=0, skip_existing=True):
					submission: Submission = submission
					if submission is None:
						logging.debug("No New Submissions, continuing...")
						time.sleep(5)
						continue

					logging.info(f"Submission {submission} found")
					reddit_data: RedditData = self.prompt_handler.handle_submission(submission)
					prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
					q = {'id': submission.id, 'name': self.me.name, 'prompt': prompt, 'type': 'submission'}
					self.queue.put(q)
					# self.do_thing(q)
					time.sleep(5)
					continue

			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				time.sleep(5)
				continue

	def poll_for_content_creation(self):
		logging.info(f"Starting Submission Process For {self.me} and monitoring {self.subreddit}")
		interval_between_posts = 60 * 8
		submission_store = dict()

		allowed = os.environ["AllowSubmissions"].split(",")
		for pair in allowed:
			name_time = pair.split(":")
			sub_name = name_time[0]
			time_interval = int(name_time[1])
			submission_store[sub_name] = time_interval

		while True:
			dt = datetime.datetime.now(timezone.utc)
			utc_time = dt.replace(tzinfo=timezone.utc)
			utc_timestamp = utc_time.timestamp()
			submissions = self._get_latest_submission()
			if len(submissions) == 0:
				logging.debug(f"No New Submissions Found {self.subreddit.display_name}")
				time.sleep(60)
				continue
			for latest_submission in submissions:
				time_interval = (utc_timestamp - latest_submission.created_utc) // 60
				if time_interval > interval_between_posts:
					for sub in submission_store.keys():
						logging.info(f"Sending Out Submission For {self.me} on {sub}")
						is_attempting = True
						while is_attempting:
							it_worked = self._create_text_post(sub)
							if it_worked:
								logging.info(f"Sent Submission To Subreddit {sub}")
								is_attempting = False
								continue
							else:
								logging.info(f"Failed to send submission")
								continue

	def _should_reply(self, comment: Comment) -> bool:
		random_reply_value = random.randint(0, self.reply_threshold)
		random_expected_valued = random.randint(0, self.reply_threshold)
		body = comment.body or ""
		triggered: int = len([item for item in self.tigger_words if body.lower().__contains__(item.lower())])
		if triggered > 0:
			logging.info(f"Triggered")
			return True

		submission: Submission = comment.submission

		submission_author: Redditor = submission.author

		if submission_author.name == self.me.name:
			return True

		if self._get_grand_parent(comment) == self.me.name:
			return random.randint(1, 2) == 2

		if random_reply_value == random_expected_valued:
			logging.info(f"Random Reply Value: {random_reply_value} and Expected Value: {random_expected_valued}")
			return True

		else:
			logging.debug(f"Reply Value {random_reply_value} is not equal random value {self.reply_threshold}. Skipping...")
			return False

	def _get_latest_submission(self):
		return list(self.reddit.redditor(self.me.name).submissions.new(limit=1))

	def _create_text_post(self, sub_name: str) -> bool:
		try:
			text_generation = ModelTextGenerator(self.me.name)
			data = text_generation.generate_text_post(sub_name)
			logging.info(f"Sending Out Submission to {sub_name}")
			self.reddit.subreddit(sub_name).submit(**data)
			return True
		except Exception as e:
			logging.error(e)
			return False

	@staticmethod
	def _get_grand_parent(comment: Comment) -> str:
		try:
			parent: RedditBase = comment.parent()
			if isinstance(parent, Comment):
				grand_parent = parent.parent()
				grand_parent_author: Redditor = grand_parent.author
				return grand_parent_author.name
			if isinstance(parent, Submission):
				submission_author: Redditor = parent.author
				return submission_author.name
		except Exception as e:
			logging.error(f"Error Trying to Get Grandparent: {e}")
			return "Exception"

	@staticmethod
	def do_thing(q):
		import torch
		import praw
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