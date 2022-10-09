import logging
import os
import random
import time

from praw import Reddit
from praw.models import Redditor, Submission, Comment, Subreddit

from shared_code.handlers.tagging_handler import TaggingHandler
from shared_code.tagging.reddit_data import RedditData
from shared_code.text_generation.text_generation import ModelTextGenerator


class StreamPolling(object):
	def __init__(self, reddit: Reddit, subreddit: Subreddit):
		self.reddit: Reddit = reddit
		self.subreddit = subreddit
		self.me: Redditor = self.reddit.user.me()
		self.prompt_handler: TaggingHandler = TaggingHandler(self.reddit)
		self.reply_threshold = int(os.environ["ReplyThreshold"])
		self.tigger_words: [str] = [item.lower() for item in os.environ["TriggerWords"].split(",")]

	def _should_reply(self, comment: Comment) -> bool:
		random_reply_value = random.randint(0, 1000)
		body = comment.body or ""
		triggered: int = len([item for item in self.tigger_words if body.lower().__contains__(item.lower())])
		if triggered > 0 and self.me.name == "SportsFanGhost-Bot":
			logging.info(f"Triggered")
			return True

		# Hack for now
		if self.me.name == "SportsFanGhost-Bot":
			return False

		if random_reply_value >= self.reply_threshold:
			return True

		else:
			logging.debug(f"Reply Value {random_reply_value} is less than {self.reply_threshold}. Skipping...")
			return False

	def poll_for_comments(self):
		num_comments_seen = 0
		while True:
			try:
				logging.info(f"Starting Poll For {self.me} and monitoring {self.subreddit} Comments")
				for comment in self.subreddit.stream.comments(pause_after=0, skip_existing=True):
					comment: Comment = comment
					if comment is None:
						logging.debug("No New Comments, continuing...")
						continue

					logging.debug(f"Comment {comment} found")
					if comment.author.name == self.me.name:
						continue

					if self._should_reply(comment):
						logging.info(f"Processing Response For Comment: {comment}")
						reddit_data: RedditData = self.prompt_handler.handle_comment(comment)
						prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
						text_generation = ModelTextGenerator(self.me.name)
						text, raw_result = text_generation.generate_text(prompt)
						logging.info(f"Sending Reply For Prompt:\n\n{prompt}\n\nWith Generated Sample:\n\n{raw_result}\n\n")
						comment.reply(body=text)
						time.sleep(1)
					num_comments_seen += 1

			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				continue

	def poll_for_submissions(self):
		while True:
			try:
				logging.info(f"Starting Poll For {self.me} and monitoring {self.subreddit} Submissions")
				for submission in self.subreddit.stream.submissions(pause_after=0, skip_existing=True):
					# Hack for now
					if self.me.name == "SportsFanGhost-Bot":
						logging.debug(f"Barry Cant Talk Right Now...")
						continue
					submission: Submission = submission
					if submission is None:
						logging.debug("No New Submissions, continuing...")
						continue

					logging.info(f"Submission {submission} found")
					reddit_data: RedditData = self.prompt_handler.handle_submission(submission)
					prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
					text_generation = ModelTextGenerator(self.me.name)
					text, raw_result = text_generation.generate_text(prompt)
					logging.info(f"Sending Reply For Prompt:\n\n{prompt}\n\nWith Generated Sample:\n\n{raw_result}\n\n")
					submission.reply(body=text)
					time.sleep(1)

			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				continue