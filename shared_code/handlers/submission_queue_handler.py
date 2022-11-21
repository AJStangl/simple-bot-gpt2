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
		self.time_since_post = 0
		self.message_broker = MessageBroker()
		self.hour = 3600

	def poll_for_submission_generation(self):
		logging.info(f"Starting poll for submission generation")
		while True:
			try:
				post_types = random.choice(["text", "link"])
				messages = list(self.create_submission_message(post_type=post_types))
				for message in messages:
					m = json.dumps(message)
					self.message_broker.put_message("submission-generator", m)
					continue
				else:
					self.time_since_post -= self.hour
					time.sleep(self.hour)
					continue
			finally:
				self.time_since_post -= self.hour
				time.sleep(self.hour)
				continue

	def create_submission_message(self, post_type):
		subs = self.subreddit.display_name.split("+")
		for sub in subs:
			logging.info(f"Creating Submission Message For {post_type}")
			yield {
				"name": self.reddit.user.me().name,
				"subreddit": sub,
				"type": post_type
			}
