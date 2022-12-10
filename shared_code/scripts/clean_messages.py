if __name__ == '__main__':
	from dotenv import load_dotenv
	from shared_code.messaging.message_sender import MessageBroker

	load_dotenv()
	broker = MessageBroker()
	for i in range(0, 2000):
		m = broker.get_message("message-generator")
		broker.delete_message("message-generator", m)
	exit(0)