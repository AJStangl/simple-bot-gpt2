import logging
import time
from multiprocessing import Process, Queue

import pbfaw as praw
import torch
from pbfaw.reddit import Comment, Submission

from shared_code.text_generation.text.text_generation import ModelTextGenerator


class QueueHandler:
	def __init__(self, queue: Queue):
		self.queue: Queue = queue
		self.time_since_post = 60

	@staticmethod
	def reply_to_thing(q):
		logger = logging.getLogger("QueueHandler")
		logger.setLevel(logging.WARNING)
		logger.info(":: Starting New Process Language Generation Process")
		print(f":: Starting New Process Language Generation Process")
		name = q.get("name")
		prompt = q.get("prompt")
		thing_id = q.get("id")
		thing_type = q.get("type")
		generator = ModelTextGenerator(name, torch.cuda.is_available())
		instance = praw.Reddit(site_name=name, ratelimit_seconds=600)
		if thing_type == "comment":
			text, raw_text = generator.generate_text(prompt)
			comment: Comment = instance.comment(id=thing_id)
			reply = comment.reply(body=text)
			if reply:
				print(f":: Successfully replied to comment {thing_id}")
				print(f":: Finished Language Generation Process...Cleaning up")
				del generator, instance
				return None
			else:
				raise Exception(f":: Failed to reply to comment {thing_id}")

		if thing_type == "submission":
			text, raw_text = generator.generate_text(prompt)
			submission: Submission = instance.submission(id=thing_id)
			reply = submission.reply(body=text)
			if reply:
				print(f":: Successfully replied to submission {thing_id}")
				print(f":: Finished Language Generation Process...Cleaning up")
				del generator, instance
				return None
			else:
				raise Exception(f":: Failed To Reply To Submission")

	def poll_for_reply(self):
		while True:
			logging.info(f"Number Of Items In Queue: {self.queue.qsize()}, processing next item")
			q = self.queue.get()
			if q:
				p = Process(target=self.reply_to_thing, args=(q,))
				p.start()
				time.sleep(10)
				p.join()
				logging.info(f":: Finished Processing Queue Item")
			continue
		time.sleep(10)
