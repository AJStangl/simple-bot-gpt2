import logging
import os
import random
import re
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
		self.text_generation = ModelTextGenerator()

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

					logging.info(f"Comment {comment} found")
					if comment.author.name == self.me.name:
						continue

					if random.randint(0, 100) >= int(os.environ["ReplyThreshold"]):
						reddit_data: RedditData = self.prompt_handler.handle_comment(comment)
						prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
						text = self.text_generation.generate_text(prompt)
						logging.info(f"Sending Reply with reply:\n {text}\nFor Prompt: {prompt}")
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
					submission: Submission = submission
					if submission is None:
						logging.debug("No New Submissions, continuing...")
						continue

					logging.info(f"Submission {submission} found")
					reddit_data: RedditData = self.prompt_handler.handle_submission(submission)
					prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
					text: str = self.text_generation.generate_text(prompt)
					logging.info(f"Sending Reply with reply:\n {text}\nFor Prompt: {prompt}")
					submission.reply(body=text)
					time.sleep(1)

			except Exception as e:
				logging.error(f"An exception has occurred {e}")
				continue
