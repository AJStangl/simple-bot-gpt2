from typing import Optional

from praw import Reddit
from praw.models import Comment, Redditor, Submission
from praw.models.reddit.base import RedditBase

from shared_code.tagging.reddit_data import RedditData
from shared_code.tagging.tags import Tags


class TaggingHandler:
	def __init__(self, reddit: Optional[Reddit]):
		self._reddit_instance: Optional[Reddit] = reddit
		self._tagging: Tags = Tags()

	@staticmethod
	def handle_comment(comment: Comment) -> RedditData:
		data = RedditData()

		subreddit: Reddit = comment.subreddit

		submission: Submission = comment.submission
		submission_author: Redditor = submission.author
		submission_title: str = submission.title

		comment_body: str = comment.body

		if submission.is_self:
			submission_content: str = submission.selftext
		else:
			submission_content: str = submission.url

		comment_author: Redditor = comment.author

		parent: RedditBase = comment.parent()
		parent_author: Redditor = parent.author

		grand_parent_author = None
		parent_comment = None

		if isinstance(parent, Comment):
			parent_comment = parent.body
			parent: Comment = parent

			grand_parent = parent.parent()
			grand_parent_author = grand_parent.author.name

		if isinstance(parent, Submission):
			parent: Submission = parent
			grand_parent: Submission = parent
			grand_parent_author = grand_parent.author.name

		data.subreddit = subreddit
		data.submission_title = submission_title
		data.submission_content = submission_content
		data.parent_author = parent_author
		data.submission_author = submission_author
		data.parent_comment = parent_comment
		data.comment_body = comment_body
		data.comment_author = comment_author
		data.grand_parent_author = grand_parent_author

		return data

	@staticmethod
	def handle_submission(submission: Submission) -> RedditData:
		data = RedditData()

		subreddit: Reddit = submission.subreddit
		submission_author: Redditor = submission.author
		submission_title: str = submission.title

		if submission.is_self:
			submission_content: str = submission.selftext
		else:
			submission_content: str = submission.url

		parent: Submission = submission
		grand_parent: Submission = parent
		grand_parent_author = grand_parent.author.name

		data.subreddit = subreddit
		data.submission_title = submission_title
		data.submission_content = submission_content
		data.parent_author = None
		data.submission_author = submission_author
		data.parent_comment = None
		data.comment_body = None
		data.comment_author = None
		data.grand_parent_author = grand_parent_author

		return data

	def create_training_from_data(self, reddit_data: RedditData) -> str:
		# First create some context for discussion
		tagged_submission = self._tagging.tag_submission(
			subreddit=reddit_data.subreddit,
			is_own_submission=reddit_data.is_submission_author(reddit_data.comment_author),
			is_link_submission=reddit_data.is_link(),
			title=reddit_data.submission_title,
			body=reddit_data.submission_content
		)

		# For training the comment is the reply and the parent is the comment. If there is no parent then it's a reply
		# Directly to a link post.
		parent_comment = None
		if reddit_data.parent_comment is not None:
			parent_comment = self._tagging.tag_comment(
				submission_author=reddit_data.submission_author,
				comment_author=reddit_data.parent_author,
				parent_author=reddit_data.grand_parent_author,
				grandparent_author="NO-PARENT",
				# To be internally consistent if we will assign the grandparent to a constant
				body=reddit_data.parent_comment,
				include_author=True  # For a parent comment we will choose to include the author.
			)

		# The reply comment in the context of training is as defined but we choose to not include the author
		reply_comment = self._tagging.tag_comment(
			submission_author=reddit_data.submission_author,
			comment_author=reddit_data.comment_author,
			parent_author=reddit_data.parent_author,
			grandparent_author=reddit_data.grand_parent_author,
			body=reddit_data.comment_body,
			include_author=False
		)

		result = tagged_submission
		if parent_comment:
			result += parent_comment

		result += reply_comment

		# In this specific context we can ignore the generation of an ending tag.
		return result

	def create_prompt_from_data(self, reddit_data: RedditData) -> str:
		# Grab an instance of the bot replying
		reply_author = self._reddit_instance.user.me().name

		# Then create some context for discussion
		tagged_submission = self._tagging.tag_submission(
			subreddit=reddit_data.subreddit,
			is_own_submission=reddit_data.is_submission_author(reply_author),
			is_link_submission=reddit_data.is_link(),
			title=reddit_data.submission_title,
			body=reddit_data.submission_content
		)

		# If the incoming data does not have a comment body, we assume it is a submission
		if reddit_data.comment_body is None:
			result = tagged_submission
			result += self._tagging.get_comment_reply_tag(
				submission_author=reddit_data.submission_author,
				grand_parent_author=None,
				parent_author=None,
				comment_author=None,
				reply_author=reply_author
			)
			return result

		# In the case of a prompt we assume that there is no reply_comment, that is what we are making. So after we establish
		# the base context we will treat the comment as the parent.
		parent_comment = self._tagging.tag_comment(
				submission_author=reddit_data.submission_author,
				comment_author=reddit_data.comment_author,
				parent_author=reddit_data.parent_author,
				grandparent_author=reddit_data.grand_parent_author,
				# To be internally consistent if we will assign the grandparent to a constant
				body=reddit_data.comment_body,
				include_author=True  # For a parent comment we will choose to include the author.
			)

		# Finally, we will include the reply tag for prompt generation. This will inform us of the correct tag to use.
		reply_tag = self._tagging.get_comment_reply_tag(
			submission_author=reddit_data.submission_author,
			grand_parent_author=reddit_data.grand_parent_author,
			parent_author=reddit_data.parent_author,
			reply_author=reply_author,
			comment_author=reddit_data.comment_author
		)

		# in the case of a submission, we are not handling that here; but, it would simply be the context with the reply
		# tag
		result = tagged_submission
		result += parent_comment
		result += reply_tag
		return result
