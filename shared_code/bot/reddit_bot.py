import logging
import os
import random
import re
import sys
import threading
import time

import praw
from praw import Reddit
from praw.models import Redditor, Submission, Comment

from shared_code.handlers.tagging_handler import TaggingHandler
from shared_code.tagging.reddit_data import RedditData
from shared_code.text_generation.text_generation import ModelTextGenerator


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.me: Redditor = self.reddit.user.me()
		self.subreddit = self.reddit.subreddit(subreddit)
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True)
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True)
		self.text_generation = ModelTextGenerator()
		self.prompt_handler: TaggingHandler = TaggingHandler(self.reddit)

	def poll_for_comments(self):
		num_comments_seen = 0
		while True:
			try:
				logging.info(f":: Starting Poll For {self.me} and monitoring {self.subreddit} Comments")
				for comment in self.subreddit.stream.comments(pause_after=0, skip_existing=True):
					comment: Comment = comment
					if comment is None:
						logging.debug(":: No New Comments, continuing...")
						continue

					logging.info(f":: Comment {comment} found")
					if comment.author.name == self.me.name:
						continue

					if random.randint(0, 100) >= int(os.environ["ReplyThreshold"]):
						reddit_data: RedditData = self.prompt_handler.handle_comment(comment)
						tagged_text: str = self.prompt_handler.create_prompt_from_data(reddit_data)
						print(tagged_text)
					# 	text = self.text_generation.generate_text(prompt)
					# 	cleaned = re.sub(r'(\<\|[\w\/ ]*\|\>)', ' ', text).strip()
						logging.info(f":: Sending Reply")
					# 	comment.reply(body=text)
						time.sleep(1)
					num_comments_seen += 1

			except Exception as e:
				logging.error(f":: An exception has occurred {e}")
				continue

	def poll_for_submissions(self):
		while True:
			try:
				logging.info(f":: Starting Poll For {self.me} and monitoring {self.subreddit} Submissions")
				for submission in self.subreddit.stream.submissions(pause_after=0, skip_existing=True):
					submission: Submission = submission
					if submission is None:
						logging.debug(":: No New Submissions, continuing...")
						continue

					logging.info(f":: Submission {submission} found")
					reddit_data: RedditData = self.prompt_handler.handle_submission(submission)
					prompt: str = self.prompt_handler.create_prompt_from_data(reddit_data)
					print(prompt)
					# 	text = self.text_generation.generate_text(prompt)
					# 	cleaned = re.sub(r'(\<\|[\w\/ ]*\|\>)', ' ', text).strip()
					logging.info(f":: Sending Reply To Submission")
					# 	submission.reply(body=text)
					time.sleep(1)

			except Exception as e:
				logging.error(f":: An exception has occurred {e}")
				continue

	def run(self):
		self.comment_polling_thread.start()
		self.submission_polling_thread.start()

	@staticmethod
	def stop():
		sys.exit(0)

