import pandas
from dotenv import load_dotenv
from sqlalchemy.orm import Session, Query

from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow
from shared_code.handlers.tagging_handler import TaggingHandler
from shared_code.tagging.reddit_data import RedditData

load_dotenv()


class TrainingDataGenerator:
	def __init__(self):
		self._context: Context = Context()
		self._session: Session = self._context.get_session()
		self._tagging_handler: TaggingHandler = TaggingHandler(reddit=None)

	def generate_training_data(self, x) -> str:
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

		tagged_data = self._tagging_handler.create_training_from_data(data)
		return tagged_data

	def run(self, redditor: str, out_file: str = "training.csv"):
		query: Query = self._session.query(TrainingDataRow).where(TrainingDataRow.CommentAuthor == redditor)
		df = pandas.read_sql(query.statement, query.session.bind)
		training = df.apply(self.generate_training_data, axis=1)
		df["TrainingString"] = df.apply(self.generate_training_data, axis=1)
		df.to_csv(f"{redditor}-{out_file}")
