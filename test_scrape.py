import time

from shared_code.clients.push_shift_client import PushShiftClient
from shared_code.fine_tuning.persistence.context import Context
import logging

from dotenv import load_dotenv
import logging

from dotenv import load_dotenv

from shared_code.clients.push_shift_client import PushShiftClient
from shared_code.fine_tuning.persistence.context import Context
from shared_code.fine_tuning.persistence.training_row import TrainingDataRow
from shared_code.tagging.reddit_data import RedditData

context = Context()
db_session = context.get_session()

load_dotenv()

logger = logging.getLogger("training")


def main():

	client: PushShiftClient = PushShiftClient()
	before = None
	i = 0
	while True:
		comments: dict = client.get_author_comments("ReallyRickAstley", before=before)
		if not comments:
			break
		all_comment_ids: [str] = [comment.get('id') for comment in comments]
		found_comment_ids = context.search_by_id(all_comment_ids, db_session)
		remaining_comments_ids = [item for item in all_comment_ids if item not in found_comment_ids]
		logger.info(f"{len(remaining_comments_ids)} from current batch {len(comments)} remains...")
		for comment in comments:
			before = comment['created_utc']
			if comment.get('id') not in remaining_comments_ids:
				continue
			else:
				data_row: TrainingDataRow = client.handle_comment(comment)
				result = context.add(data_row, db_session)
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


if __name__ == '__main__':
	redditor = "ReallyRickAstley"
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	main()
