import logging
import os
import time

import click
from dotenv import load_dotenv

from shared_code.bot.reddit_bot import RedditBot

load_dotenv()


@click.group()
def cli1():
	pass


@click.group()
def cli2():
	pass


@click.group()
def cli3():
	pass


@cli1.command()
@click.option("--bot-name", prompt='specify the bot name. Must be present in the praw.ini file', default='')
@click.option("--sub-reddit",
			  prompt='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+THE_Pablop+SubSimGPT2Interactive',
			  default='CoopAndPabloPlayHouse')
@click.option("--model", prompt='specify the path to the model to use. Example. /mnt/models/foo-bot/', default=None)
def run_bot(bot_name: str, sub_reddit: str):
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{bot_name}|%(message)s', level=logging.INFO)
	bot = RedditBot(bot_name, sub_reddit)
	bot.run()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info('Shutdown')
		bot.stop()


cli = click.CommandCollection(sources=[cli1, cli2, cli3])

if __name__ == '__main__':
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{os.environ["BotName"]}|%(message)s',
						level=logging.INFO)
	cli()
