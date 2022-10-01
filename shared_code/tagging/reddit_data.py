class RedditData(object):
	def __init__(self,
				 subreddit=None,
				 submission_title=None,
				 submission_content=None,
				 parent_author=None,
				 submission_author=None,
				 parent_comment=None,
				 comment_body=None,
				 comment_author=None,
				 grand_parent_author=None):

		self.subreddit = subreddit
		self.submission_title = submission_title
		self.submission_content = submission_content
		self.parent_author = parent_author
		self.submission_author = submission_author
		self.parent_comment = parent_comment
		self.comment_body = comment_body
		self.comment_author = comment_author
		self.grand_parent_author = grand_parent_author

	def is_link(self):
		if self.submission_content is None:
			return False
		return self.submission_content.startswith("https://")
