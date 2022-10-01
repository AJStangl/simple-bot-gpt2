from typing import Optional

from praw import Reddit
from praw.models import Comment, Redditor, Submission
from praw.models.reddit.base import RedditBase

from shared_code.tagging.reddit_data import RedditData
from shared_code.tagging.tags import Tags


class CommentHandler:
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
		parent_comment = parent.body

		grand_parent_author = None
		if isinstance(parent, Comment):
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

	def tag_comment_for_reply(self, reddit_data: RedditData, reply_author=None, add_reply_tag=True) -> str:

		if self._reddit_instance is not None:
			reply_author: Redditor = self._reddit_instance.user.me()
			reply_author_name = reply_author.name
		else:
			reply_author_name = reply_author

		tagged_submission = self._tagging.tag_submission(
			subreddit=reddit_data.subreddit,
			is_link_submission=reddit_data.is_link(),
			title=reddit_data.submission_title,
			body=reddit_data.submission_content
		)

		is_comment_reply = reddit_data.parent_comment is not None
		tagged_parent = None
		if is_comment_reply:
			tagged_parent = self._tagging.tag_comment(
			submission_author=reddit_data.submission_author,
			comment_author=reddit_data.parent_author,
			parent_author=reddit_data.parent_author,
			grandparent_author=reddit_data.grand_parent_author,
			body=reddit_data.parent_comment,
			include_author=True)

		tagged_comment = self._tagging.tag_comment(
			submission_author=reddit_data.submission_author,
			comment_author=reddit_data.comment_author,
			parent_author=reddit_data.parent_author,
			grandparent_author=reddit_data.grand_parent_author,
			body=reddit_data.comment_body,
			include_author=(add_reply_tag is True)
		)

		reply_tag = self._tagging.get_comment_reply_tag(
			submission_author=reddit_data.submission_author,
			grand_parent_author=reddit_data.grand_parent_author,
			parent_author=reddit_data.parent_author,
			reply_author=reply_author_name,
			comment_author=reddit_data.comment_author
		)

		result = f"{tagged_submission}"

		if tagged_parent is not None:
			result += tagged_parent

		result += tagged_comment

		if add_reply_tag:
			result += reply_tag

		return result

