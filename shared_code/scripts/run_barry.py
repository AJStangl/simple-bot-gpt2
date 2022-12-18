if __name__ == '__main__':
	from dotenv import load_dotenv
	import json
	from shared_code.messaging.message_sender import MessageBroker
	import praw
	import random

	SUBMISSION_LIMIT = 100
	load_dotenv()

	bots = ["SportsFanBotGhostGPT"]
	# post_type = ["text", "link"]
	post_type = ["image"]
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