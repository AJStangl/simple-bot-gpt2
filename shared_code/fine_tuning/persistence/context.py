import logging
import os
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from shared_code.fine_tuning.persistence.training_row import Base, TrainingDataRow


class Context:

	def __init__(self):
		self._user = os.environ['PsqlUser']
		self._password = os.environ['PsqlPassword']
		self._engine = create_engine(f"postgresql://{self._user}:{self._password}@localhost:5432/redditData", pool_size=32, max_overflow=-1)

	def get_session(self):
		return Session(self._engine)

	def close_session(self, session: Session):
		session.close()

	@staticmethod
	def add(entity: Base, session: Session) -> Union[TrainingDataRow, None]:
		try:
			existing_record = session.get(type(entity), entity.CommentId)
			if existing_record:
				logging.debug(f":: Record Exists for type {type(entity)} and Id {entity.CommentId}")
				return existing_record
			session.add(entity)
			session.commit()
			return None
		except Exception as e:
			logging.error(f":: An exception has occurred in method `Add` with message {e}")
		finally:
			pass

	@staticmethod
	def exists(comment_id: str, session: Session) -> bool:
		existing_record = session.get(TrainingDataRow, comment_id)
		if existing_record:
			return True
		else:
			return False

	@staticmethod
	def search_by_id(comment_ids: [str], session: Session) -> [str]:
		query = session.query(TrainingDataRow.CommentId).filter(TrainingDataRow.CommentId.in_(comment_ids))
		result = list(session.execute(query).scalars())
		return result

