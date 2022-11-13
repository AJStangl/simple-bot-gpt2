import gc
import json
import logging
import time
from multiprocessing import Process

import praw
import torch
from praw.reddit import Comment, Submission

from shared_code.messaging.message_sender import MessageBroker
from shared_code.text_generation.text.text_generation import ModelTextGenerator


class ReplyProcess:
	def __init__(self):
		self.message_broker = MessageBroker()

	def poll_for_reply(self):
		logging.info(f"Starting poll_for_reply")
		while True:
			try:
				message = self.message_broker.get_message("message-generator")
				if message:
					content = message.content
					q = json.loads(content)
					logging.info(f"Processing Message: {q}")
					p = Process(target=self.reply_to_thing, args=(q,), daemon=True)
					p.start()
					p.join()
					logging.info(f"Finished Processing Queue Item")
			finally:
				time.sleep(10)

	@staticmethod
	def reply_to_thing(q: dict):
		logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
		logging.info(f"Call To Create New Reply To Comment")
		generator = None
		instance = None
		try:
			logging.info(f"Starting New Process Language Generation Process")
			name = q.get("name")
			prompt = q.get("prompt")
			thing_id = q.get("id")
			thing_type = q.get("type")
			generator = ModelTextGenerator(name, torch.cuda.is_available())
			instance = praw.Reddit(site_name=name)
			if thing_type == "comment":
				text, raw_text = generator.generate_text(prompt)
				comment: Comment = instance.comment(id=thing_id)
				reply = comment.reply(body=text)
				if reply:
					logging.info(f"Successfully replied to comment {thing_id} -- with {text}")
					return
				else:
					logging.info(f"Failed to reply to comment {thing_id}")
					return

			if thing_type == "submission":
				text, raw_text = generator.generate_text(prompt)
				submission: Submission = instance.submission(id=thing_id)
				reply = submission.reply(body=text)
				if reply:
					logging.info(f"Successfully replied to submission {thing_id} ==	")
					return
				else:
					logging.info(f"Failed To Reply To Submission")
					return
		except Exception as e:
			logging.info(f"Exception Occurred: {e} attempting to reply")
			return
		finally:
			del generator, instance
			torch.cuda.empty_cache()
			gc.collect()