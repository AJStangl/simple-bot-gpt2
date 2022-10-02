import logging

import praw
import prawcore
import requests
from dotenv import load_dotenv
from praw import exceptions
from praw.reddit import Comment, Reddit, Submission
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3 import Retry

from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow

load_dotenv()

logger = logging.getLogger("training")


class RedditDataCollection:
	def __init__(self):
		self.context: Context = Context()
		self.db_session: Session = self.context.get_session()
		self.session = requests.Session()
		self.adapter = HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1, allowed_methods=None, status_forcelist=[429, 500, 502, 503, 504]))
		self.session.mount("https://", self.adapter)
		self.reddit = Reddit(site_name="Yuli-Ban-Bot-GPT2")

	def get_grandparent_author(self, comment: Comment):
		# First get the comment and load the parent
		try:
			grand_parent = comment.parent().parent()
			return grand_parent.author.name
		except:
			return None

	def get_author_comments(self, author, **kwargs):
		base_address = 'https://api.pushshift.io/reddit'
		r = self.session.get(
			f"{base_address}/comment/search/?author={author}&sort=desc&sort_type=created_utc&filter=created_utc,parent_id,permalink,id,author,subreddit",
			params=kwargs)
		logger.info(r.url)
		try:
			data = r.json()
			return data['data']
		except Exception as e:
			logger.error(f":: {e} in getting author")
			return {}

	def run(self):
		i = 0
		before = None
		while True:
			comments: dict = self.get_author_comments(author="GusterIs4Lovers", before=before, limit=100)
			if not comments: break

			for comment in comments:
				before = comment['created_utc']
				parent_id = comment.get('parent_id')
				perma_link = comment.get('permalink')
				comment_id = comment.get('id')

				if self.context.exists(comment_id, self.db_session):
					continue

				try:
					# /r/foo/submissionId/bar-baz/commentId
					submission_id = perma_link.split('/')[4]
				except IndexError:
					continue

				parent_body = None
				parent_author = "Unknown"

				submission_title = None
				submission_content = None
				submission_author = "Unknown"

				comment_author = comment.get("author")
				subreddit = comment.get("subreddit")

				# First load a non-dirty copy of the reddit
				comment: Comment = self.reddit.comment(id=comment_id)

				grand_parent_author = self.get_grandparent_author(comment)

				try:
					comment_body = comment.body
				except praw.exceptions.ClientException:
					continue

				if parent_id.__contains__("t1"):
					try:
						comment_parent_id = parent_id.split('_')[1]
						parent_comment: Comment = self.reddit.comment(id=comment_parent_id)
						parent_body = parent_comment.body
						parent_submission: Submission = self.reddit.submission(id=parent_comment.submission.id)
						submission_title = parent_submission.title
						submission_author = parent_submission.author.name
						if parent_submission.is_self:
							submission_content = parent_submission.selftext
						else:
							submission_content = parent_submission.url

						parent_author = parent_comment.author.name
						parent_id = parent_comment.id

					except AttributeError:
						continue
					except praw.exceptions.ClientException:
						continue
					except praw.exceptions.PRAWException:
						continue
					except prawcore.PrawcoreException:
						continue
					except IndexError:
						continue

				if parent_id.__contains__("t3"):
					try:
						submission_parent_id = parent_id.split('_')[1]
						parent_submission: Submission = self.reddit.submission(id=submission_parent_id)
						submission_title = parent_submission.title
						submission_author = parent_submission.author.name
						if parent_submission.is_self:
							submission_content = parent_submission.selftext
						else:
							submission_content = parent_submission.url

						parent_author = parent_submission.author.name

						parent_id = parent_submission.id

					except AttributeError:
						continue
					except praw.exceptions.ClientException:
						continue
					except praw.exceptions.PRAWException:
						continue
					except prawcore.PrawcoreException:
						continue
					except IndexError:
						continue

				row = TrainingDataRow()
				row.Subreddit = subreddit
				row.SubmissionId = submission_id
				row.SubmissionTitle = submission_title
				row.SubmissionAuthor = submission_author
				row.SubmissionContent = submission_content
				row.ParentId = parent_id
				row.ParentAuthor = parent_author
				row.ParentBody = parent_body
				row.CommentId = comment_id
				row.CommentBody = comment_body
				row.CommentAuthor = comment_author
				row.GrandParentAuthor = grand_parent_author
				result = self.context.add(row, self.db_session)
				if result is None:
					logger.info(f"Added {i} rows")
					i += 1
				else:
					continue
			logger.info("Continuing...")
		logger.info("Complete")
		return before


if __name__ == '__main__':
	logging.basicConfig(format=':: %(thread)s|%(asctime)s|%(message)s', level=logging.INFO)
	collector: RedditDataCollection = RedditDataCollection()
	try:
		collector.run()
	finally:
		collector.context.close_session(collector.db_session)
