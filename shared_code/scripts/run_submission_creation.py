if __name__ == '__main__':
	from dotenv import load_dotenv
	import json
	from shared_code.messaging.message_sender import MessageBroker
	import time
	import praw
	import random

	SUBMISSION_LIMIT = 100
	load_dotenv()

	bots = ["LauraBotGPT", "SportsFanBotGhostGPT", "LauraBotGPT", "AustinBotGPT", "NickBotGPT", "CriagBotGPT"]
	post_type = ["image", "text", "link"]
	subs = ["CoopAndPabloPlayHouse", "SubSimGPT2Interactive"]


	while True:
		random.shuffle(subs)
		for sub in subs:
			bot = random.choice(bots)
			topic_type = random.choice(post_type)
			reddit = praw.Reddit(site_name=bot)
			print(f"Sending message to queue for {bot} with post type: {topic_type} to sub {sub}")
			message = {
				"name": bot,
				"subreddit": sub,
				"type": topic_type,
			}
			broker = MessageBroker()
			broker.put_message("submission-generator", json.dumps(message))
			time.sleep(10 * 3)
		time.sleep(60 * 60 * 4)
