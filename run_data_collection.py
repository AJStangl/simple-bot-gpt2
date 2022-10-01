import logging
import os

import praw
import prawcore
import requests
from praw import exceptions
from praw.models.reddit.base import RedditBase
from praw.reddit import Comment, Reddit, Submission, Redditor
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3 import Retry
from dotenv import load_dotenv
from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow

load_dotenv()
logger = logging.getLogger("training")

context: Context = Context()
db_session: Session = context.get_session()

session = requests.Session()

adapter = HTTPAdapter(max_retries=Retry(total=4, backoff_factor=1, allowed_methods=None, status_forcelist=[429, 500, 502, 503, 504]))

session.mount("https://", adapter)

reddit = Reddit(site_name="")


def get_grandparent_author(comment: Comment):
	# First get the comment and load the parent
	try:
		grand_parent = comment.parent().parent()
		# Check if the parent is a comment
		# if isinstance(parent, Comment):
		# 	parent: Comment = parent
		# 	# Get the grandparent
		# 	grand_parent = parent.parent()
		# 	# We don't care if the grandparent is a sub or a comment, we simply want the author
		# 	author: Redditor = grand_parent.author
		# 	return author.name
		# else:
		# 	# Otherwise if the parent is a submission then simply take the author
		# 	parent: Submission
		# 	author: Redditor = parent.author
		# 	return author.name
		return grand_parent.author.name
	except:
		return None


def get_author_comments(author, **kwargs):
	base_address = 'https://api.pushshift.io/reddit'
	r = session.get(
		f"{base_address}/comment/search/?author={author}&sort=asc&sort_type=created_utc&filter=created_utc,parent_id,permalink,id,author,subreddit",
		params=kwargs)
	logger.info(r.url)
	try:
		data = r.json()
		return data['data']
	except Exception as e:
		logger.error(f":: {e} in getting author")
		return {}


def main():
	i = 0
	before = None
	while True:
		comments: dict = get_author_comments(author="Yuli-Ban", before=before, limit=100)
		if not comments: break

		for comment in comments:
			before = comment['created_utc']
			parent_id = comment.get('parent_id')
			perma_link = comment.get('permalink')
			comment_id = comment.get('id')

			if context.exists(comment_id, db_session):
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
			comment: Comment = reddit.comment(id=comment_id)

			grand_parent_author = get_grandparent_author(comment)

			try:
				comment_body = comment.body
			except praw.exceptions.ClientException:
				continue

			if parent_id.__contains__("t1"):
				try:
					comment_parent_id = parent_id.split('_')[1]
					parent_comment: Comment = reddit.comment(id=comment_parent_id)
					parent_body = parent_comment.body
					parent_submission: Submission = reddit.submission(id=parent_comment.submission.id)
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
					parent_submission: Submission = reddit.submission(id=submission_parent_id)
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
			result = context.add(row, db_session)
			if result is None:
				logger.info(f":: Added {i} rows")
				i += 1
			else:
				continue
		logger.info(":: Continuing...")
	logger.info(":: Complete")
	return before


if __name__ == '__main__':
	logging.basicConfig(format='%(message)s', level=logging.INFO)
	try:
		main()
	finally:
		context.close_session(db_session)
