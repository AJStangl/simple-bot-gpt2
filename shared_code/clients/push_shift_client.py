import json
import logging
import time
from encodings.utf_8 import decode
from typing import Union

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from shared_code.models.training_row import TrainingDataRow
from shared_code.models.reddit_data import RedditData

load_dotenv()
logger = logging.getLogger("PushShiftClient")

BODY = "body"


class PushShiftClient:
	def __init__(self):
		self.__session: requests.Session = requests.Session()
		self.__adapter: HTTPAdapter = HTTPAdapter(max_retries=Retry(total=5, backoff_factor=0.1, allowed_methods=False,
																	status_forcelist=[429, 500, 502, 503, 504]))
		self.__session.mount("https://", self.__adapter)
		self.__base_address: str = 'https://api.pushshift.io/reddit'
		self.__reddit_base_address: str = 'https://www.reddit.com/'

	def get_by_reddit_id(self, reddit_id: str, attempts: int = 0, max_attempts: int = 10):
		requests_address = f"{self.__reddit_base_address}/{reddit_id}.json"
		target_data = None
		if max_attempts > attempts:
			attempts += 1
			# noinspection PyBroadException
			try:
				response = requests.get(requests_address, headers={"accept": "application/json; charset=UTF-8",
																   "user-agent": "localhost"})
				if response.status_code == 429:
					logger.info("To many requests...Sleeping for 10")
					time.sleep(10)
					return self.get_by_reddit_id(reddit_id, attempts)
				data = self.__handle_response(response, False)
				for item in data:
					if item is not None:
						children = item.get("data").get("children")
						if children:
							for child in children:
								kind = child.get("kind")
								if kind == "t3":
									sub_data = child.get("data")
									target_data = sub_data
									time.sleep(1)
									return target_data
								time.sleep(1)

			except Exception as e:
				logger.error(e)
				time.sleep(1)
				return target_data

	def get_comment_by_id(self, comment_id: str, fields=None, attempts: int = 0, max_attempts: int = 10) -> Union[
		None, dict]:
		"""
		Searches for a comment by a given id
		:param max_attempts:
		:param attempts: Force recursive re-try attempt
		:param comment_id: The comment id
		:param fields: Parameters to specify filtering on
		:return: The inner data object of the api response or none
		"""
		if max_attempts > attempts:
			request_address = f"{self.__base_address}/comment/search?ids={comment_id}"
			if fields:
				request_address += f"&fields={fields}"
			try:
				result = self.__handle_response(self.__session.get(request_address))[0]
				return result
			except IndexError as index_error:
				logger.error(f":: IndexError in get_comment_by_id for {comment_id}\t{index_error}")
				return {}
			except Exception as e:
				logger.error(f":: Exception in get_comment_by_id for {comment_id}\t{e}")
				attempts += 1
				logger.info(f":: Current attempt: {attempts}")
				time.sleep(1)
				return self.get_comment_by_id(comment_id, attempts=attempts)
		else:
			return {}

	def get_submission_by_id(self, submission_id: str, fields=None, attempts: int = 0, max_attempts: int = 10) -> dict:
		"""
		Searches for a submission by a given id
		:param max_attempts:
		:param attempts:
		:param submission_id: The submission id
		:param fields: Parameters to specify filtering on
		:return: The inner data object of the api response or none
		"""
		request_address = f"{self.__base_address}/search/submission?ids={submission_id}"
		if fields:
			request_address += f"&fields={fields}"
		if max_attempts > attempts:
			try:
				response = self.__session.get(request_address)
				handled = self.__handle_response(response)
				if len(handled) > 0:
					return handled[0]
				else:
					attempts += 1
					return self.get_submission_by_id(submission_id, attempts=attempts)
			except Exception as e:
				logger.error(f":: Exception in get_comment_by_id for {submission_id}\t{e}")
				attempts += 1
				return self.get_submission_by_id(submission_id, attempts=attempts)
		else:
			return {}

	def get_author_comments(self, author, before, fields=None) -> Union[None, dict]:
		request_address = f"{self.__base_address}/comment/search/?author={author}&sort=desc&sort_type=created_utc&limit=100"
		if before:
			request_address += f"&before={before}"
		if fields:
			request_address += f"&fields={fields}"
		try:
			return self.__handle_response(self.__session.get(request_address))
		except Exception as e:
			logger.error(f":: Exception in get_comment_by_id for {author}\t{e}")
			raise requests.RequestException("Error in get_author_comments")

	def get_author_submissions(self, author, fields=None) -> Union[None, dict]:
		request_address = f"{self.__base_address}/submission/search/?author={author}&sort=desc&sort_type=created_utc"
		if fields:
			request_address += f"&fields={fields}"
		try:
			return self.__handle_response(self.__session.get(request_address))
		except Exception as e:
			logger.error(f":: Exception in get_author_submissions for {author}\t{e}")
			return None

	def __handle_response(self, response: requests.Response, do_format=True) -> [{}]:
		"""
		Handles the general loading of data from a response object to the dict. If it fails None is returned
		:param response: The API response provided by the invocation of the session
		:return: A dictionary object of the data
		"""
		if response.status_code != 200:
			logger.info(f":: Status Code: {response.status_code}")
			return []

		try:
			out, errors = decode(response.content)
			final = json.loads(out)
			if do_format:
				loaded = self.__try_get_data(final)
				return loaded
			return final
		except Exception as e:
			logger.error(f":: Exception in handling the api response with: {e}")
			return []

	@staticmethod
	def __try_get_data(data: dict) -> [{}]:
		"""
		A try/except wrapper for extracting the data out of the push shift api response
		:param data: An object assumed to have a key 'data'
		:return: Returns the inner data member.
		"""
		# noinspection PyBroadException
		try:
			ret_val = data.get("data")
			return ret_val
		except Exception:
			return [{}]

	@staticmethod
	def _get_parent_id(data: dict) -> Union[None, dict]:
		"""
		Gets the parent id from a single data dict and partitions on the delimiter "_". If this operation fails it will
		return none. Other-wise it will return {'type': 't_*', 'parent_id': 'abc123'}
		:param data: A comment push shift object that is assumed to have a key 'parent_id'
		:return:  A dictionary object 'type': 't_*', 'parent_id': 'abc123'  where t_* is the type of parent (comment or submission). None if the operation fails.
		"""
		parent_id = data.get("parent_id") or ""
		if isinstance(parent_id, int):
			return {}
		if parent_id == "":
			return {}
		# This is a top level comment. We cant do anything about this...
		reply_type, sep, parent = parent_id.partition("_")
		if reply_type and parent:
			data = {"type": reply_type, "parent_id": parent}
			return data
		return {}

	@staticmethod
	def _get_submission_id_by_link_id(link_id: str) -> Union[None, str]:
		"""
		Partitions on the link id
		:param link_id: t3_foo
		:return: foo or None
		"""
		reply_type, sep, parent = link_id.partition("_")
		if reply_type and parent:
			return parent
		return None

	def handle_comment(self, comment: dict) -> TrainingDataRow:
		data_point: RedditData = RedditData()

		# Meta
		parent_id = None

		# Comment Level Data
		comment_id = comment.get("id")
		link_id = comment.get("link_id")

		data_point.comment_score = comment.get("score")

		data_point.comment_body = comment.get("body")
		data_point.comment_author = comment.get("author")
		data_point.subreddit = comment.get("subreddit")

		# Submission Level Data
		data_point.submission_author = None
		data_point.submission_content = None
		data_point.submission_title = None

		data_point.parent_author = None
		data_point.parent_comment = None

		data_point.grand_parent_author = None

		parent_id_dict = self._get_parent_id(comment)

		submission_id = self._get_submission_id_by_link_id(link_id)
		if submission_id:
			sub_data = self.get_by_reddit_id(submission_id)
			if sub_data:
				data_point.submission_author = sub_data.get("author")
				data_point.submission_title = sub_data.get("title")
				data_point.submission_title = sub_data.get("title")
				if sub_data.get("is_self"):
					data_point.submission_content = sub_data.get('selftext')
				else:
					data_point.submission_content = sub_data.get("url")

		# If we have a return from out partitioned parent_id...
		if parent_id_dict:
			parent_type = parent_id_dict.get("type")
			parent_id = parent_id_dict.get("parent_id")
			# We only care if the parent is a comment...
			if parent_type == "t1":
				# grab an instance of the parent comment
				parent_comment = self.get_comment_by_id(comment_id=parent_id)
				data_point.parent_comment = parent_comment.get("body")
				data_point.parent_author = parent_comment.get("author")
				# then get the grandparent author.
				grand_parent_id_dict = self._get_parent_id(parent_comment)
				# there exists a grandfather comment that is not a submission. We want this author...
				if grand_parent_id_dict and grand_parent_id_dict.get("type") == "t1":
					grand_parent_comment = self.get_comment_by_id(comment_id=parent_id)
					data_point.grand_parent_author = grand_parent_comment.get("author")

		row = TrainingDataRow()
		row.Subreddit = data_point.subreddit
		row.SubmissionId = submission_id
		row.SubmissionTitle = data_point.submission_title
		row.SubmissionAuthor = data_point.submission_author
		row.SubmissionContent = data_point.submission_content
		row.ParentId = parent_id
		row.ParentAuthor = data_point.parent_author
		row.ParentBody = data_point.parent_comment
		row.CommentId = comment_id
		row.CommentBody = data_point.comment_body
		row.CommentAuthor = data_point.comment_author
		row.GrandParentAuthor = data_point.grand_parent_author
		row.CommentScore = data_point.comment_score

		return row
