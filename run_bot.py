import logging
import os
import time

from dotenv import load_dotenv
from shared_code.bot.reddit_bot import RedditBot

load_dotenv()

#TODO: Shift to cli command
bot_name = os.environ["BotName"]
sub_reddit = os.environ["Sub"]


if __name__ == '__main__':
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{os.environ["BotName"]}|%(message)s', level=logging.INFO)
	bot = RedditBot(bot_name, sub_reddit)
	bot.run()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info('Shutdown')
		bot.stop()
