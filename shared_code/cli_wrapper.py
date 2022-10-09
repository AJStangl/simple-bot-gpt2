import logging
import os

import click
from dotenv import load_dotenv

from shared_code.app.generate_training_data import TrainingDataGenerator
from shared_code.app.reddit_data_collection import RedditDataCollection
from shared_code.app.run_bot import BotRunner

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
@click.option("--sub-reddit", prompt='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+THE_Pablop+SubSimGPT2Interactive', default='CoopAndPabloPlayHouse')
@click.option("--reply-rate", prompt='The base rate at which a bot will randomly reply. N / 1000', default='9000')
def run_bot(bot_name: str, sub_reddit: str, reply_rate: str):
	# Global setting
	os.environ["ReplyThreshold"] = reply_rate
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{bot_name}|{sub_reddit}|:: %(message)s', level=logging.INFO)
	BotRunner.run_bot(bot_name, sub_reddit)


@cli2.command()
@click.option("--redditor", prompt='The name of the redditor to collect data on', default='generic')
def collect_data(redditor: str):
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{redditor}|:: %(message)s', level=logging.INFO)
	RedditDataCollection().run(redditor)


@cli3.command()
@click.option("--redditor", prompt='The name of the redditor to collect data on', default='generic')
def create_training(redditor: str):
	logging.basicConfig(format=f':: Thead:%(thread)s|%(asctime)s|{redditor}|:: %(message)s', level=logging.INFO)
	TrainingDataGenerator().run(redditor)


cli = click.CommandCollection(sources=[cli1, cli2, cli3])

if __name__ == '__main__':
	cli()
