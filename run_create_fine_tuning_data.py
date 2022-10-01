import os
from dotenv import load_dotenv
import pandas
from sqlalchemy.orm import Session, Query

from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow
from shared_code.handlers.comment_handler import CommentHandler
from shared_code.tagging.reddit_data import RedditData

load_dotenv()

context: Context = Context()
session: Session = context.get_session()
comment_handler: CommentHandler = CommentHandler(None)

def get_submission_context(subreddit: str, submission_title: str, submission_content: str, parent_author: str, submission_author: str):
	if submission_content.startswith("https://"):
		if parent_author == submission_author:
			return f'<|sooss r/{subreddit}|><|sot|>{submission_title}<|soost|>{submission_content}'
		return f'<|soss r/{subreddit}|><|sot|>{submission_title}<|sost|>{submission_content}'
	else:
		if parent_author == submission_author:
			return f'<|sools r/{subreddit}|><|sot|>{submission_title}<|sool|>{submission_content}'
		return f'<|sols r/{subreddit}|><|sot|>{submission_title}<|sol|>{submission_content}'


def get_reply_context(parent_comment, reply_comment: str, submission_author: str, comment_author: str, parent_author: str):
	if submission_author == comment_author:
		# start_reply_tag = f'<|soopr u/{comment_author}|>'
		end_reply_tag = '<|eoopr|>'
	else:
		# start_reply_tag = f"<|sor u/{comment_author}|>"
		end_reply_tag = '<|eor|>'

	start_reply_tag = "<|sor|>"

	parent_reply_tag = f"<|sor u/{parent_author}|>"
	parent_end_reply_tag = '<|eor|>'

	if parent_comment is None or parent_comment == "":
		return f"{start_reply_tag}{reply_comment}{end_reply_tag}"

	return f"{parent_reply_tag}{parent_comment}{parent_end_reply_tag}{start_reply_tag}{reply_comment}{end_reply_tag}"


def generate_training_row(x) -> str:
	submission_context: str = get_submission_context(x.Subreddit, x.SubmissionTitle, x.SubmissionContent, x.ParentAuthor, x.SubmissionAuthor)
	reply_context: str = get_reply_context(x.ParentBody, x.CommentBody, x.SubmissionAuthor, x.CommentAuthor, x.ParentAuthor)
	return f"{submission_context}{reply_context}"

def gen_new(x) -> str:
	foo = CommentHandler(None)

	data = RedditData()

	subreddit = x.Subreddit
	submission_title = x.SubmissionTitle
	submission_content = x.SubmissionContent
	parent_author = x.ParentAuthor
	submission_author = x.SubmissionAuthor
	parent_comment = x.ParentBody
	comment_body = x.CommentBody
	comment_author = x.CommentAuthor
	grand_parent_author = x.GrandParentAuthor

	data.subreddit = subreddit
	data.submission_title = submission_title
	data.submission_content = submission_content
	data.parent_author = parent_author
	data.submission_author = submission_author
	data.parent_comment = parent_comment
	data.comment_body = comment_body
	data.comment_author = comment_author
	data.grand_parent_author = grand_parent_author

	tagged_data = foo.tag_comment_for_reply(data, x.CommentAuthor, add_reply_tag=False)
	return tagged_data


if __name__ == '__main__':
	query: Query = session.query(TrainingDataRow).where(TrainingDataRow.CommentAuthor == "Yuli-Ban")
	df = pandas.read_sql(query.statement, query.session.bind)
	training = df.apply(gen_new, axis=1)
	for elem in list(training):
		print(elem)
	# df["TrainingString"] = df.apply(generate_training_row, axis=1)
	# df.to_csv("training.csv")

