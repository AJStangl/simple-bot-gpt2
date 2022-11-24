import typing


class Tags(object):
	_open_tag: str = '<|'
	_close_tag: str = '|>'

	link_submission_start_tag: str = 'sols'
	link_submission_end_tag: str = 'eols'

	own_start_of_link_tag = 'osol'  # new tag -- Not backwards compatible
	own_end_of_link_tag = 'oeol'   # new tag -- Not Backwards compatible

	start_of_link_tag = 'sol'
	end_of_link_tag = 'eol'

	own_text_submission_start_tag: str = 'ososs'  # new tag -- Not backwards compatible
	own_text_submission_end_tag: str = 'oeoss'    # new tag -- Not backwards compatible

	text_submission_start_tag: str = 'soss'
	text_submission_end_tag: str = 'eoss'

	title_start_tag: str = 'sot'
	title_end_tag: str = 'eot'

	text_start_tag: str = 'sost'
	text_end_tag: str = 'eost'

	simple_reply_start_tag: str = 'sor'
	simple_reply_end_tag: str = 'eor'

	post_reply_start_tag: str = 'soopr'
	post_reply_end_tag: str = 'eoopr'

	own_content_start_tag: str = 'soocr'
	own_content_end_tag: str = 'eoocr'


class Tagger(Tags):
	"""
	Main class for performing tagging operations.
	"""

	def _create_tag(self, tag_type: str):
		"""
		Creates a tag <|foo|>
		:param tag_type: The type of tag
		:return: String with properly formatted tag
		"""
		return f"{self._open_tag}{tag_type}{self._close_tag}"

	def get_comment_reply_tag(self, submission_author: str, grand_parent_author: typing.Optional[str],
							  parent_author: typing.Optional[str], comment_author: typing.Optional[str],
							  reply_author: typing.Optional[str]) -> str:
		"""
		Creates a tag for a comment reply
		:param submission_author: The author of the submission
		:param grand_parent_author:  The author 2 levels up from the original comment
		:param parent_author:  The author 1 level up from the original comment
		:param comment_author:  The author of the comment
		:param reply_author: The author of the reply
		:return: String with properly formatted tag
		"""

		if submission_author == reply_author:
			return self._create_tag(self.own_content_start_tag)

		if grand_parent_author == reply_author:
			return self._create_tag(self.post_reply_start_tag)

		if parent_author == reply_author:
			return self._create_tag(self.simple_reply_start_tag)

		if comment_author == reply_author:
			return self._create_tag(self.simple_reply_start_tag)

		else:
			return self._create_tag(self.simple_reply_start_tag)

	def create_submission_tag(self, link_post: bool, subreddit: str) -> str:
		"""
		Creates a tag for a submission
		:param link_post: Indication if the submission is a link post. Creates an image like post
		:param subreddit: The subreddit to which the submission is posted
		:return: String with properly formatted tag for a submission
		"""
		if link_post:
			return f"{self._open_tag}{self.link_submission_start_tag} r/{subreddit}{self._close_tag}{self._create_tag(self.title_start_tag)}"
		else:
			return f"{self._open_tag}{self.text_submission_start_tag} r/{subreddit}{self._close_tag}{self._create_tag(self.title_start_tag)}"

	def tag_submission(self, subreddit: str, is_link_submission: bool, is_own_submission: bool, title: str, body: str):
		"""
		Tag a submission
		:param subreddit: The subreddit to which the submission is posted
		:param is_link_submission: Indication if the submission is a link post. Changes the start tag
		:param is_own_submission:  Indication if the submission is posted by the bot. Changes the start tag
		:param title: The title of the submission
		:param body: The body of the submission
		:return: The tagged submission
		"""
		tag: str = f"{self._open_tag}"
		subreddit = "GusterAtCarnegie"

		if is_own_submission and is_link_submission:
			tag += f"{self.own_start_of_link_tag} r/{subreddit}{self._close_tag}"
			tag += f"{self._create_tag(self.title_start_tag)}{title}{self._create_tag(self.title_end_tag)}{self._create_tag(self.start_of_link_tag)}{self._create_tag(self.end_of_link_tag)}"
			return tag

		if is_own_submission and not is_link_submission:
			tag += f"{self.own_text_submission_start_tag} r/{subreddit}{self._close_tag}"
			tag += f"{self._create_tag(self.title_start_tag)}{title}{self._create_tag(self.title_end_tag)}{self._create_tag(self.text_start_tag)}{body}{self._create_tag(self.text_end_tag)}"
			return tag

		# <|foo r/bar|>
		if is_link_submission:
			tag += f"{self.link_submission_start_tag} r/{subreddit}{self._close_tag}"
			tag += f"{self._create_tag(self.title_start_tag)}{title}{self._create_tag(self.title_end_tag)}{self._create_tag(self.start_of_link_tag)}{self._create_tag(self.end_of_link_tag)}"
			return tag
		else:
			tag += f"{self.text_submission_start_tag} r/{subreddit}{self._close_tag}"
			tag += f"{self._create_tag(self.title_start_tag)}{title}{self._create_tag(self.title_end_tag)}{self._create_tag(self.text_start_tag)}{body}{self._create_tag(self.text_end_tag)}"
			return tag

	def tag_comment(self, submission_author: str, comment_author: str, parent_author: str, grandparent_author: str,
					body: str, include_author: bool):
		"""
		Tag a comment
		:param submission_author: The submission author
		:param comment_author:  The comment author
		:param parent_author: The parent comment author
		:param grandparent_author: The grandparent comment author
		:param body: The body of the comment
		:param include_author: Include the author in the tag
		:return: A tagged comment
		"""
		subreddit = "GusterAtCarnegie"
		tag: str = f"{self._open_tag}"
		if submission_author == comment_author:
			tag += f"{self.post_reply_start_tag}"
			if include_author:
				tag += f" u/{comment_author}"
			tag += f"{self._close_tag}"
			tag += f"{body}"
			tag += f"{self._create_tag(self.post_reply_end_tag)}"
			return tag

		if grandparent_author == comment_author:
			tag += f"{self.own_content_start_tag}"
			if include_author:
				tag += f" u/{comment_author}"
			tag += f"{self._close_tag}"
			tag += f"{body}"
			tag += f"{self._create_tag(self.own_content_end_tag)}"
			return tag

		if parent_author == comment_author:
			tag += f"{self.own_content_start_tag}"
			if include_author:
				tag += f" u/{comment_author}"
			tag += f"{self._close_tag}"
			tag += f"{body}"
			tag += f"{self._create_tag(self.own_content_end_tag)}"
			return tag

		else:
			tag += f"{self.simple_reply_start_tag}"
			if include_author:
				tag += f" u/{comment_author}"
			tag += f"{self._close_tag}"
			tag += f"{body}"
			tag += f"{self._create_tag(self.simple_reply_end_tag)}"
			return tag
