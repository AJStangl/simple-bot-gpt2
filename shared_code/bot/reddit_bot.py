import logging
import sys
import threading
import time

import praw
from praw import Reddit
from praw.models import Redditor, Submission, Comment


class RedditBot:
	def __init__(self, bot_name: str, subreddit):
		self.reddit: Reddit = praw.Reddit(site_name=bot_name)
		self.me: Redditor = self.reddit.user.me()
		self.subreddit = self.reddit.subreddit(subreddit)
		self.comment_polling_thread = threading.Thread(target=self.poll_for_comments, args=(), daemon=True)
		self.submission_polling_thread = threading.Thread(target=self.poll_for_submissions, args=(), daemon=True)

	def poll_for_comments(self):
		while True:
			try:
				logging.info(f":: Starting Poll For {self.me} and monitoring {self.subreddit} Comments")
				for comment in self.subreddit.stream.comments(pause_after=0, skip_existing=True):
					comment: Comment = comment
					if comment is None:
						logging.debug(":: No New Comments, continuing...")
						continue

					logging.info(f":: Comment {comment} found")
					time.sleep(1)
					print(comment.body)

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
					print(submission.title, submission.selftext)
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

