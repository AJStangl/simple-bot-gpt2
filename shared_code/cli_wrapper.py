import logging
import os
import time

import click
from dotenv import load_dotenv

from shared_code.app.reddit_data_collection import RedditDataCollection
from shared_code.app.run_bot import BotRunner
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
	BotRunner.run_bot(bot_name, sub_reddit)


@cli2.command()
@click.option("--redditor", prompt='The name of the redditor to collect data on', default='generic')
def collect_data(redditor: str):
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|%(message)s', level=logging.INFO)
	RedditDataCollection().run(redditor)


cli = click.CommandCollection(sources=[cli1, cli2, cli3])

if __name__ == '__main__':
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{os.environ["BotName"]}|%(message)s', level=logging.INFO)
	cli()
