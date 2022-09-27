class RedditData(object):
	def __init__(self, subreddit, submission_title, submission_content, parent_author, submission_author, parent_comment, reply_comment, comment_author):
		self.subreddit = subreddit
		self.submission_title = submission_title
		self.submission_content = submission_content
		self.parent_author = parent_author
		self.submission_author = submission_author
		self.parent_comment = parent_comment
		self.reply_comment = reply_comment
		self.comment_author = comment_author


class Tagging:

	def get_submission_context(self, subreddit: str, submission_title: str, submission_content: str, parent_author: str, submission_author: str):
		if submission_content.startswith("https://"):
			if parent_author == submission_author:
				return f'<|sooss r/{subreddit}|><|sot|>{submission_title}<|soost|>{submission_content}'
			return f'<|soss r/{subreddit}|><|sot|>{submission_title}<|sost|>{submission_content}'
		else:
			if parent_author == submission_author:
				return f'<|sools r/{subreddit}|><|sot|>{submission_title}<|sool|>{submission_content}'
			return f'<|sols r/{subreddit}|><|sot|>{submission_title}<|sol|>{submission_content}'

	def get_reply_context(self, parent_comment, reply_comment: str, submission_author: str, comment_author: str, parent_author: str):
		if submission_author == comment_author:
			end_reply_tag = '<|eoopr|>'
		else:
			end_reply_tag = '<|eor|>'

		start_reply_tag = "<|sor|>"

		parent_reply_tag = f"<|sor u/{parent_author}|>"
		parent_end_reply_tag = '<|eor|>'

		if parent_comment is None or parent_comment == "":
			return f"{start_reply_tag}"

		return f"{parent_reply_tag}{parent_comment}{parent_end_reply_tag}{start_reply_tag}"

	def generate_training_row(self, x: RedditData) -> str:
		submission_context: str = self.get_submission_context(x.subreddit, x.submission_title, x.submission_content, x.parent_author, x.submission_author)
		reply_context: str = self.get_reply_context(x.parent_comment, x.reply_comment, x.submission_author, x.comment_author, x.parent_author)
		return f"{submission_context}{reply_context}"
