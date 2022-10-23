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

from shared_code.clients.push_shift_client import PushShiftClient
from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow

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
			comments: dict = self.client.get_author_comments(author_name, before=before)
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
