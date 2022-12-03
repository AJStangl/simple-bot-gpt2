import logging
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

	def poll_for_submission_generation(self):
		logging.info(f"Starting poll for submission generation")
		while True:
			try:
				time.sleep(60)
				continue
			except Exception as e:
				logging.info(f"An exception has occurred {e}")
				time.sleep(60)
				continue
			finally:
				time.sleep(60)
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
