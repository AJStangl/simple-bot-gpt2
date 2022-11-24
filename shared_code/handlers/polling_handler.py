import json
import logging
import os
import random
import time

from praw import Reddit
from praw.models import Redditor, Submission, Comment, Subreddit
from praw.models.reddit.base import RedditBase

from shared_code.tagging.tagging_handler import TaggingHandler
from shared_code.messaging.message_sender import MessageBroker
from shared_code.models.reddit_data import RedditData


class StreamPolling(object):
	def __init__(self, reddit: Reddit, subreddit: Subreddit):
		self.MAX_SLEEP_TIME = 10
		self.REPLY_SLEEP_TIME = 10
		self.reddit: Reddit = reddit
		self.subreddit = subreddit
		self.me: Redditor = self.reddit.user.me()
		self.prompt_handler: TaggingHandler = TaggingHandler(self.reddit)
		self.reply_threshold = int(os.environ["ReplyThreshold"])
		self.tigger_words: [str] = [item.lower() for item in os.environ["TriggerWords"].split(",")]
		self.banned_words: [str] = [item.lower() for item in os.environ["BannedWords"].split(",")]
		self.message_broker: MessageBroker = MessageBroker()
		# self.reply_probability: ReplyProbability = ReplyProbability(self.me)

	def poll_for_submissions(self):
		logging.info(f"Starting poll for submissions for {self.me.name}")
		while True:
			try:
				submission_stream = self.subreddit.stream.submissions(pause_after=0, skip_existing=True)
				for submission in submission_stream:
					self._handle_submission(submission)
					continue
			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				continue
			finally:
				time.sleep(self.MAX_SLEEP_TIME)

	def poll_for_comments(self):
		logging.info(f"Starting poll for comments for {self.me.name}")
		while True:
			try:
				comment_stream = self.subreddit.stream.comments(pause_after=0, skip_existing=True)
				for comment in comment_stream:
					self._handle_comment(comment)
					continue
			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				continue
			finally:
				time.sleep(self.MAX_SLEEP_TIME)

	def _handle_comment(self, comment: Comment) -> None:
		try:
			comment: Comment = comment
			if comment is None:
				logging.debug(f"Incoming Comment for {self.me.name} is None... Skipping")
				return

			if comment.author.name == self.me.name:
				return

			if self._should_reply(comment):
				logging.info(f"Processing Response For Comment: {comment} for {self.me.name}")
				reddit_data: RedditData = self.prompt_handler.handle_comment(comment)
				prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
				q = {'id': comment.id, 'name': self.me.name, 'prompt': prompt, 'type': 'comment'}
				m = json.dumps(q)
				self.message_broker.put_message("message-generator", m)
				return

			else:
				logging.debug(f"No processing comment for {self.me.name}")
				return

		except Exception as e:
			logging.error(f"An exception has occurred {e} while handling comment {comment} for {self.me.name}")
			return

		finally:
			time.sleep(self.REPLY_SLEEP_TIME)

	def _handle_submission(self, submission: Submission) -> None:
		try:
			submission: Submission = submission
			if submission is None:
				logging.debug(f"Incoming Submission for {self.me.name} is None... Skipping")
				return

			logging.info(f"Processing Response For Submission: {submission} for {self.me.name}")
			reddit_data: RedditData = self.prompt_handler.handle_submission(submission)
			prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
			q = {'id': submission.id, 'name': self.me.name, 'prompt': prompt, 'type': 'submission'}
			m = json.dumps(q)
			self.message_broker.put_message("message-generator", m)
			return

		except Exception as e:
			logging.error(f"An exception has occurred {e}")
			return

	def _should_reply(self, comment: Comment) -> bool:
		random_reply_value = random.randint(0, self.reply_threshold)
		random_expected_valued = random.randint(0, self.reply_threshold)
		body = comment.body or ""
		triggered: int = len([item for item in self.tigger_words if body.lower().__contains__(item.lower())])
		if triggered > 0:
			logging.info(f"Triggered")
			return True

		banned: int = len([item for item in self.banned_words if body.lower().__contains__(item.lower())])
		if banned > 0:
			logging.info(f"Banned Word Encountered")
			return False

		submission: Submission = comment.submission

		submission_author: Redditor = submission.author

		if submission_author.name == self.me.name:
			return True

		if self._get_grand_parent(comment) == self.me.name:
			return random.randint(1, 2) == 2

		# reply_probability: float = self.reply_probability.calculate_reply_probability(comment)
		# random_value = random.random()
		#
		# if random_value < reply_probability:
		# 	logging.info(f"{comment} Random value {random_value:.3f} is < reply probability {(reply_probability):.3f}. Starting a reply..")
		# 	return True
		# else:
		# 	logging.info(f"{comment} Random value {random_value:.3f} is not < reply probability {(reply_probability):.3f}. No reply.. :(")
		if random_reply_value == random_expected_valued:
			logging.info(f"Random Reply Value: {random_reply_value} and Expected Value: {random_expected_valued}")
			return True

		else:
			logging.debug(
				f"Reply Value {random_reply_value} is not equal random value {self.reply_threshold}. Skipping...")
			return False

	def _get_latest_submission(self):
		return list(self.reddit.redditor(self.me.name).submissions.new(limit=1))

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
