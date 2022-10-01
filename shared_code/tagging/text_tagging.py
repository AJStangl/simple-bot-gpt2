from shared_code.handlers.comment_handler import TaggingHandler
from shared_code.tagging.reddit_data import RedditData


class Tagging:

	@staticmethod
	def get_submission_context(subreddit: str, submission_title: str, submission_content: str, parent_author: str, submission_author: str):
		if submission_content.startswith("https://"):
			if parent_author == submission_author:
				return f'<|sooss r/{subreddit}|><|sot|>{submission_title}<|soost|>{submission_content}'
			return f'<|soss r/{subreddit}|><|sot|>{submission_title}<|sost|>{submission_content}'
		else:
			if parent_author == submission_author:
				return f'<|sools r/{subreddit}|><|sot|>{submission_title}<|sool|>{submission_content}'
			return f'<|sols r/{subreddit}|><|sot|>{submission_title}<|sol|>{submission_content}'

	@staticmethod
	def get_reply_context(parent_comment, reply_comment: str, submission_author: str, comment_author: str, parent_author: str):
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
		pass
		# foo = TaggingHandler(None)
		# data = RedditData()
		# data.subreddit = subreddit
		# data.submission_title = submission_title
		# data.submission_content = submission_content
		# data.parent_author = parent_author
		# data.submission_author = submission_author
		# foo.tag_comment_for_reply(data)
		# return foo
		# submission_context: str = self.get_submission_context(x.subreddit, x.submission_title, x.submission_content, x.parent_author, x.submission_author)
		# reply_context: str = self.get_reply_context(x.parent_comment, x.reply_comment, x.submission_author, x.comment_author, x.parent_author)
		# return f"{submission_context}{reply_context}"
