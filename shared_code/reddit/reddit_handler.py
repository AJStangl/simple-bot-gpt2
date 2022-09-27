from praw import Reddit
from praw.reddit import Comment

from shared_code.text_generation.text_tagging import RedditData


class RedditHandler:
	def __init__(self, reddit):
		self.reddit: Reddit = reddit

	def process_comment(self, comment: Comment) -> RedditData:
		data: RedditData = RedditData("", "", "", "", "", "","","")
		data.subreddit = comment.subreddit.display_name
		data.submission_title = comment.submission.title

		if comment.submission.is_self:
			data.submission_content = comment.submission.selftext
		else:
			data.submission_content = comment.submission.url

		parent = comment.parent()
		data.parent_author = parent.author
		data.submission_author = comment.submission.author.name
		try:
			data.parent_comment = parent.body
		except Exception:
			pass

		data.comment_author = self.reddit.user.me().name
		return data


