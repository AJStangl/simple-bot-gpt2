if __name__ == '__main__':
	from dotenv import load_dotenv
	import json
	from shared_code.messaging.message_sender import MessageBroker
	import time
	import praw
	import random

	SUBMISSION_LIMIT = 100
	load_dotenv()

	bots = ["LauraBotGPT, SportsFanBotGhostGPT", "LauraBotGPT", "AustinBotGPT", "NickBotGPT", "CriagBotGPT"]
	post_type = ["image"] #, "text", "link"]
	while True:
		bot = random.choice(bots)
		topic_type = random.choice(post_type)
		reddit = praw.Reddit(site_name=bot)
		print(f"Sending message to queue for {bot} with post type: {topic_type}")
		message = {
			"name": bot,
			"subreddit": "CoopAndPabloPlayHouse",
			"type": topic_type,
		}
		broker = MessageBroker()
		broker.put_message("submission-generator", json.dumps(message))
		time.sleep(60 * 60 * 2)