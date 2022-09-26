import os
import sys
import time
from dotenv import load_dotenv

from shared_code.bot.reddit_bot import RedditBot
import logging

load_dotenv()

def main():
	bot = RedditBot(os.environ["BotName"], os.environ["Sub"])
	bot.run()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info('Shutdown')
		bot.stop()


if __name__ == '__main__':
	logging.basicConfig(format='%(message)s', level=logging.INFO)
	main()



