import logging
import time

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from shared_code.clients.push_shift_client import PushShiftClient
from shared_code.fine_tuning.persistence.context import Context
from shared_code.models.training_row import TrainingDataRow

load_dotenv()

logger = logging.getLogger("training")


class Collector:
	client: PushShiftClient = PushShiftClient()
	context: Context = Context()

	def __init__(self):
		self.session: Session = self.context.get_session()

	def get_author_comments(self, author_name: str):
		before = None
		i = 0
		while True:
			try:
				comments: dict = self.client.get_author_comments(author_name, before=before)
			except requests.RequestException as e:
				logger.error(e)
				time.sleep(10)
				continue
			if not comments:
				break
			all_comment_ids: [str] = [comment.get('id') for comment in comments]
			found_comment_ids = self.context.search_by_id(all_comment_ids, self.session)
			remaining_comments_ids = [item for item in all_comment_ids if item not in found_comment_ids]
			logger.info(f"{len(remaining_comments_ids)} from current batch {len(comments)} remains...")
			for comment in comments:
				before = comment['created_utc']
				if comment.get('id') not in remaining_comments_ids:
					continue
				else:
					data_row: TrainingDataRow = self.client.handle_comment(comment)
					result = self.context.add(data_row, self.session)
					if result is None:
						logger.info(f"Added {i} rows")
						i += 1
					else:
						logger.info(f"Nothing was updated for Comment {data_row.CommentId}")
						continue
					time.sleep(1)
			logger.info("Continuing...")
		logger.info("Complete")
		return before

	def get_author_submissions(self, author_name):
		before = None
		i = 0
		while True:
			try:
				submissions: dict = self.client.get_author_submissions(author_name, before=before)
			except requests.RequestException as e:
				logger.error(e)
				time.sleep(10)
				continue
			if not submissions:
				break
			all_submission_ids: [str] = [submission.get('id') for submission in submissions]
			found_submission_ids = self.context.search_by_id(all_submission_ids, self.session)
			remaining_submissions_ids = [item for item in all_submission_ids if item not in found_submission_ids]
			logger.info(f"{len(remaining_submissions_ids)} from current batch {len(submissions)} remains...")
			for submission in submissions:
				before = submission['created_utc']
				if submission.get('id') not in remaining_submissions_ids:
					continue
				else:
					data_row: TrainingDataRow = self.client.handle_submission(submission)
					result = self.context.add(data_row, self.session)
					if result is None:
						logger.info(f"Added {i} rows")
						i += 1
					else:
						logger.info(f"Nothing was updated for Comment {data_row.CommentId}")
						continue
					time.sleep(1)
			logger.info("Continuing...")
		logger.info("Complete")
		return before