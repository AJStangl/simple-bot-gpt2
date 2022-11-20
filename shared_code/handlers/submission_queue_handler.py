import json
import logging
import random
import time

from praw.reddit import Reddit

from shared_code.messaging.message_sender import MessageBroker


# TODO: Move this and the above method to different handler
class SubmissionCreationHandler(object):
	def __init__(self, reddit: Reddit, subreddit):
		self.reddit: Reddit = reddit
		self.subreddit = subreddit
		self.time_since_post = 0 # 1 hour
		self.message_broker = MessageBroker()

	def poll_for_submission_generation(self):
		logging.info(f"Starting poll_for_submission_generation")
		post_types = random.choice(["text", "link"])
		while True:
			try:
				if self.time_since_post <= 0:
					self.time_since_post = 60 * 60
					message = self.create_submission_message(post_type=post_types)
					for elem in message:
						m = json.dumps(elem)
						self.message_broker.put_message("submission-generator", m)
				else:
					self.time_since_post -= 30
					continue
			finally:
				self.time_since_post -= 30
				time.sleep(30)

	def create_submission_message(self, post_type):
		subs = self.subreddit.display_name.split("+")
		for sub in subs:
			logging.info(f"Creating Submission Message For {post_type}")
			yield {
				"name": self.reddit.user.me().name,
				"subreddit": sub,
				"type": post_type
			}