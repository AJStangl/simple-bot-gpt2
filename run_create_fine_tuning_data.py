import os

import pandas
from sqlalchemy.orm import Session, Query

from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow

load_dotenv()

context: Context = Context()
session: Session = context.get_session()


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


if __name__ == '__main__':
	query: Query = session.query(TrainingDataRow).where(TrainingDataRow.CommentAuthor == "Yuli-Ban")
	df = pandas.read_sql(query.statement, query.session.bind)
	training = df.apply(generate_training_row, axis=1)
	df["TrainingString"] = df.apply(generate_training_row, axis=1)
	df.to_csv("training.csv")

