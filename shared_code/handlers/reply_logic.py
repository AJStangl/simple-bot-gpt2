import praw
from praw.models import Redditor, Message
from praw.reddit import Comment, Submission
from praw import exceptions
from datetime import datetime


class ReplyLogicConfiguration(object):

	def __init__(self):
		self.own_comment_reply_boost: float = 0.2
		self.own_submission_reply_boost: float = 0.8
		self.interrogative_reply_boost: float = 1.0
		self.new_submission_reply_boost: float = 0.5
		self.human_author_reply_boost: float = 1.0
		self.bot_author_reply_boost: float = 0.5
		self.base_reply_probability: float = -0.1
		self.comment_depth_reply_penalty: float = 0.1
		self.message_mention_reply_probability: float = 1.0


class ReplyProbability:
	def __init__(self, redditor: Redditor):
		self.reply_logic_configuration: ReplyLogicConfiguration = ReplyLogicConfiguration()
		self.user: Redditor = redditor
		self._do_not_reply_bot_usernames: [str] = []
		self._negative_word_list: [str] = []

	def calculate_reply_probability(self, praw_thing) -> float:
		"""
		Calculate the probability of replying to a given PRAW Thing
		:param praw_thing:
		:return:
		"""
		if not praw_thing.author:
			# If the praw_thing has been deleted the author will be None,
			# don't proceed to attempt a reply. Usually we will have downloaded
			# the praw_thing before it is deleted so this won't get hit often.
			return 0
		elif praw_thing.author.name.lower() == self.user.name.lower():
			# The incoming praw object's author is the bot, so we won't reply
			return 0
		elif praw_thing.author.name.lower() in self._do_not_reply_bot_usernames:
			# Ignore comments/messages from Admins
			return 0

		# merge the text content into a single variable so it's easier to work with
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
			# otherwise it's a comment
			thing_text_content = praw_thing.body
			# navigate to the parent submission to get the link_flair_text
			submission_link_flair_text = praw_thing.submission.link_flair_text or ''
			submission_created_utc = datetime.utcfromtimestamp(praw_thing.submission.created_utc)
			is_own_comment_reply = praw_thing.parent().author == self.user.name

		elif isinstance(praw_thing, Message):
			thing_text_content = praw_thing.body
			submission_created_utc = datetime.utcfromtimestamp(praw_thing.created_utc)

		# TODO: Implement this
		# second most important thing is to check for a negative keyword
		# calculate whether negative keywords are in the text and return 0
		# if len(self._negative_word_list) > 0:
		# 	# The title or selftext/body contains negative keyword matches
		# 	# and we will avoid engaging with negative content
		# 	return 0

		# if the submission is flaired as a subreddit announcement,
		# do not reply so, as to not spam the sub
		if submission_link_flair_text.lower() in ['announcement']:
			return 0

		# if the bot is mentioned, or its username is in the thing_text_content, reply 100%
		if getattr(praw_thing, 'type', '') == 'username_mention' or\
			self.user.name.lower() in thing_text_content.lower() or\
			isinstance(praw_thing, Message):
			return self.reply_logic_configuration.message_mention_reply_probability

		# From here we will start to calculate the probability cumulatively
		# Adjusting the weights here will change how frequently the bot will post
		# Try not to spam the sub too much and let other bots and humans have space to post
		base_probability = self.reply_logic_configuration.base_reply_probability

		if isinstance(praw_thing, Comment):
			# Find the depth of the comment
			comment_depth = self._find_depth_of_comment(praw_thing)
			if comment_depth > 12:
				# don't reply to deep comments, to prevent bots replying in a loop
				return 0
			else:
				# Reduce the reply probability x% for each level of comment depth
				# to keep the replies higher up
				base_probability -= ((comment_depth - 1) * self.reply_logic_configuration.comment_depth_reply_penalty)

		# Check the flair and username to see if the author might be a bot
		# 'Verified GPT-2 Bot' is only valid on r/subsimgpt2interactive
		# Sometimes author_flair_text will be present but None
		if 'verified gpt-2' in (getattr(praw_thing, 'author_flair_text', '') or '').lower()\
			or any(praw_thing.author.name.lower().endswith(i) for i in ['ssi', 'bot', 'gpt2']):
			# Adjust for when the author is a bot
			base_probability += self.reply_logic_configuration.bot_author_reply_boost
		else:
			# assume humanoid if author metadata doesn't meet the criteria for a bot
			base_probability += self.reply_logic_configuration.human_author_reply_boost

		# TODO: Positive Key Words
		# if len(self._keyword_helper.positive_keyword_matches(thing_text_content)) > 0:
		# 	# A positive keyword was found, increase probability of replying
		# 	base_probability += self._positive_keyword_reply_boost

		if isinstance(praw_thing, Submission):
			# it's a brand-new submission.
			# This is mostly obsoleted by the depth penalty
			base_probability += self.reply_logic_configuration.new_submission_reply_boost

		if isinstance(praw_thing, Submission) or is_own_comment_reply:
			if any(kw.lower() in thing_text_content.lower() for kw in ['?', ' you', 'what', 'how', 'when', 'why']):
				# any interrogative terms in the submission or comment text;
				# results in an increased reply probability
				base_probability += self.reply_logic_configuration.interrogative_reply_boost

		if isinstance(praw_thing, Comment):
			if praw_thing.parent().author == self.user.name:
				# the post prior to this is by the bot
				base_probability += self.reply_logic_configuration.own_comment_reply_boost

			if praw_thing.submission.author == self.user.name:
				# the submission is by the bot, and favor that with a boost
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
		# it's a 1-based index so init the counter with 1
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
