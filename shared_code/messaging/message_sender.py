import os
import logging
from typing import Any

from azure.storage.queue import QueueMessage, QueueServiceClient, TextBase64EncodePolicy


class MessageBroker(object):
	logging.getLogger("azure.storage").setLevel(logging.WARNING)

	def __init__(self):
		self.connection_string: str = os.environ["AzureStorageConnectionString"]
		self.service: QueueServiceClient = QueueServiceClient.from_connection_string(self.connection_string,
																					 encode_policy=TextBase64EncodePolicy())
		self.queues: dict = {
			"comment": "message-generator",
			"submission": "submission-generator",
			"lock": "submission-lock"
		}

	def put_message(self, queue_name: str, content: Any, time_to_live=None) -> QueueMessage:
		if time_to_live is None:
			return self.service.get_queue_client(queue_name).send_message(content=content)
		else:
			return self.service.get_queue_client(queue_name).send_message(content=content, time_to_live=time_to_live)

	def get_message(self, queue_name: str) -> QueueMessage:
		return self.service.get_queue_client(queue_name).receive_message()

	def delete_message(self, queue_name: str, q, pop_receipt = None):
		return self.service.get_queue_client(queue_name).delete_message(q, pop_receipt)

	def clear_queue(self, queue_name: str):
		return self.service.get_queue_client(queue_name).clear_messages()

	def count_message(self, queue_name: str) -> int:
		return self.service.get_queue_client(queue_name).get_queue_properties().approximate_message_count
