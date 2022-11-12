import os
import logging
from azure.storage.queue import QueueMessage, QueueServiceClient, TextBase64EncodePolicy


class MessageBroker(object):

	logging.getLogger("azure.storage").setLevel(logging.WARNING)

	def __init__(self):
		self.connection_string: str = os.environ["AzureStorageConnectionString"]
		self.service: QueueServiceClient = QueueServiceClient.from_connection_string(self.connection_string, encode_policy=TextBase64EncodePolicy())
		self.queues: dict = {
			"generate": "message-generator",
			"send": "message-sender"
		}

	def put_message(self, queue_name: str, content) -> QueueMessage:
		return self.service.get_queue_client(queue_name).send_message(content=content)

	def get_message(self, queue_name: str) -> QueueMessage:
		return self.service.get_queue_client(queue_name).receive_message()

	def delete_message(self, queue_name: str, q):
		return self.service.get_queue_client(queue_name).delete_message(q)