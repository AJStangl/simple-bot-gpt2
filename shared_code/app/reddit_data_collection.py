import logging
import time

import praw
import prawcore
import requests
from dotenv import load_dotenv
from praw import exceptions
from praw.reddit import Comment, Reddit, Submission, Redditor
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
			parent = comment.parent()
			grand_parent = parent.parent()
			grand_parent_author = grand_parent.author
			grand_parent_author_name = grand_parent_author.name
			return grand_parent_author_name
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

	def run(self, author: str):
		i = 0
		before = None
		while True:
			comments: dict = self.get_author_comments(author=author, before=before, limit=100)
			if not comments:
				break

			all_comment_ids: [str] = [comment.get('id') for comment in comments]

			found_comment_ids = self.context.search_by_id(all_comment_ids, self.db_session)

			remaining_comments_ids = [item for item in all_comment_ids if item not in found_comment_ids]

			logger.info(f"{len(remaining_comments_ids)} from current batch {len(comments)} remains...")

			for comment in comments:
				before = comment['created_utc']
				if comment.get('id') not in remaining_comments_ids:
					continue

				logger.info(f"Processing comment {comment.get('id')}")
				parent_id = comment.get('parent_id') or ""
				perma_link = comment.get('permalink') or ""
				comment_id = comment.get('id') or ""

				try:
					# /r/foo/submissionId/bar-baz/commentId
					submission_id = perma_link.split('/')[4]
				except IndexError:
					logger.error(f"Index Error for {comment_id}")
					submission_id = "NotFound"

				parent_body = None
				parent_author = "Unknown"

				submission_title = None
				submission_content = None
				submission_author = "Unknown"

				comment_author = comment.get("author") or ""
				subreddit = comment.get("subreddit") or ""

				# First load a non-dirty copy of the reddit
				comment: Comment = self.reddit.comment(id=comment_id)

				grand_parent_author = self.get_grandparent_author(comment)

				try:
					comment_body = comment.body
				except praw.exceptions.ClientException as e:
					logger.error(f"An exception {e} has occurred for comment {comment_id}")
					continue

				if parent_id.__contains__("t1"):
					try:
						comment_parent_id = parent_id.split('_')[1]
						parent_comment: Comment = self.reddit.comment(id=comment_parent_id)
						parent_body = parent_comment.body
						parent_submission: Submission = self.reddit.submission(id=parent_comment.submission.id)
						parent_submission_author: Redditor = parent_submission.author
						submission_title = parent_submission.title
						submission_author = parent_submission_author.name
						if parent_submission.is_self:
							submission_content = parent_submission.selftext
						else:
							submission_content = parent_submission.url

						parent_author = parent_comment.author.name
						parent_id = parent_comment.id

					except AttributeError as e:
						logger.error(e)
						pass
					except praw.exceptions.ClientException as e:
						logger.error(e)
						continue
					except praw.exceptions.PRAWException as e:
						logger.error(e)
						continue
					except prawcore.PrawcoreException as e:
						logger.error(e)
						continue
					except IndexError as e:
						logger.error(e)
						continue

				if parent_id.__contains__("t3"):
					try:
						submission_parent_id = parent_id.split('_')[1]
						parent_submission: Submission = self.reddit.submission(id=submission_parent_id)
						submission_id = submission_parent_id
						submission_title: str = parent_submission.title
						parent_submission_author: Redditor = parent_submission.author
						submission_author: str = parent_submission_author.name
						if parent_submission.is_self:
							submission_content = parent_submission.selftext
						else:
							submission_content = parent_submission.url

						parent_author = parent_submission_author.name

						parent_id = parent_submission.id

					except AttributeError as e:
						logger.error(e)
						pass
					except praw.exceptions.ClientException as e:
						logger.error(e)
						continue
					except praw.exceptions.PRAWException as e:
						logger.error(e)
						continue
					except prawcore.PrawcoreException as e:
						logger.error(e)
						continue
					except IndexError as e:
						logger.error(e)
						continue

				logger.info(f"Preparing To Update {comment_id}")
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
					logger.info(f"Nothing was updated for Comment {comment_id}")
					continue
			time.sleep(1)
			logger.info("Continuing...")
		logger.info("Complete")
		return before
