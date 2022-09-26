import sys
import time

from shared_code.bot.reddit_bot import RedditBot
import logging

def main():
	bot = RedditBot("ChadNoctorBot-GPT2", "CoopAndPabloPlayHouse")
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



