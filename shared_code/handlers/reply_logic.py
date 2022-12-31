import praw
from praw.models import Redditor, Message
from praw.reddit import Comment, Submission
from praw import exceptions
from datetime import datetime


class ReplyLogicConfiguration(object):

	def __init__(self):
		self.own_comment_reply_boost: float = 0.3
		self.own_submission_reply_boost: float = 0.5
		self.interrogative_reply_boost: float = 0.6
		self.new_submission_reply_boost: float = 0.1
		self.human_author_reply_boost: float = 1.0
		self.bot_author_reply_boost: float = 0.1
		self.base_reply_probability: float = 0.3
		self.comment_depth_reply_penalty: float = 0.1
		self.message_mention_reply_probability: float = 1.0


class ReplyProbability:
	def __init__(self, redditor: Redditor):
		self.reply_logic_configuration: ReplyLogicConfiguration = ReplyLogicConfiguration()
		self.user: Redditor = redditor
		self._do_not_reply_bot_usernames: [str] = []
		self._negative_word_list: [str] = []

	# noinspection GrazieInspection
	def calculate_reply_probability(self, praw_thing) -> float:
		"""
		Calculate the probability of replying to a given PRAW Thing
		:param praw_thing:
		:return:
		"""
		if not praw_thing.author:
			return 0
		elif praw_thing.author.name.lower() == self.user.name.lower():
			return 0
		elif praw_thing.author.name.lower() in self._do_not_reply_bot_usernames:
			return 0

		# merge the text content into a single variable, so it's easier to work with
		thing_text_content = ''
		submission_link_flair_text = ''
		submission_created_utc = None
		is_own_comment_reply = False

		if isinstance(praw_thing, Submission):
			# object is a submission that has title and selftext
			thing_text_content = f'{praw_thing.title} {praw_thing.selftext}'
			submission_link_flair_text = praw_thing.link_flair_text or ''
			submission_created_utc = datetime.utcfromtimestamp(praw_thing.created_utc)

		elif isinstance(praw_thing, Comment):
			thing_text_content = praw_thing.body
			submission_link_flair_text = praw_thing.submission.link_flair_text or ''
			submission_created_utc = datetime.utcfromtimestamp(praw_thing.submission.created_utc)
			is_own_comment_reply = praw_thing.parent().author == self.user.name

		elif isinstance(praw_thing, Message):
			thing_text_content = praw_thing.body
			submission_created_utc = datetime.utcfromtimestamp(praw_thing.created_utc)

		if submission_link_flair_text.lower() in ['announcement']:
			return 0

		# if the bot is mentioned, or its username is in the thing_text_content, reply 100%
		if getattr(praw_thing, 'type', '') == 'username_mention' or\
			self.user.name.lower() in thing_text_content.lower() or\
			isinstance(praw_thing, Message):
			return self.reply_logic_configuration.message_mention_reply_probability

		base_probability = self.reply_logic_configuration.base_reply_probability

		if isinstance(praw_thing, Comment):
			comment_depth = self._find_depth_of_comment(praw_thing)
			if comment_depth > 12:
				return 0
			else:
				base_probability -= ((comment_depth - 1) * self.reply_logic_configuration.comment_depth_reply_penalty)

		# if 'verified gpt-2' in (getattr(praw_thing, 'author_flair_text', '') or '').lower() or any(praw_thing.author.name.lower().__contains__(i) for i in ['ssi', 'bot', 'gpt2', 'gpt']): # or any(praw_thing.author.name.lower().endswith(i) for i in ['ssi', 'bot', 'gpt2', 'gpt']):
			# Adjust for when the author is a bot

		else:
			# assume humanoid if author metadata doesn't meet the criteria for a bot
			base_probability += self.reply_logic_configuration.human_author_reply_boost

		if isinstance(praw_thing, Submission):
			base_probability += self.reply_logic_configuration.new_submission_reply_boost

		if isinstance(praw_thing, Submission) or is_own_comment_reply:
			if any(kw.lower() in thing_text_content.lower() for kw in ['?', ' you', 'what', 'how', 'when', 'why']):
				base_probability += self.reply_logic_configuration.interrogative_reply_boost

		if isinstance(praw_thing, Comment):
			if praw_thing.parent().author == self.user.name:
				base_probability += self.reply_logic_configuration.own_comment_reply_boost

			if praw_thing.submission.author == self.user.name:
				base_probability += self.reply_logic_configuration.own_submission_reply_boost

		reply_probability = min(base_probability, 1)

		# work out the age of submission in hours
		age_of_submission = (datetime.utcnow() - submission_created_utc).total_seconds() / 3600
		# calculate rate of decay over x hours
		rate_of_decay = max(0, 1 - (age_of_submission / 24))
		# multiply the rate of decay by the reply probability
		return round(reply_probability * rate_of_decay, 2)

	def _find_depth_of_comment(self, praw_thing) -> int:
		refresh_counter = 0
		# it's a 1-based index so init the counter with 1Ad
		depth_counter = 1
		ancestor = praw_thing
		while not ancestor.is_root:
			depth_counter += 1
			ancestor = ancestor.parent()
			if refresh_counter % 9 == 0:
				try:
					ancestor.refresh()
				except praw.exceptions.ClientException:
					return depth_counter
				refresh_counter += 1
		return depth_counter
