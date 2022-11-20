import logging
import os

import click
from dotenv import load_dotenv

from shared_code.app.bot_runner import BotRunner
from shared_code.app.generate_training_data import TrainingDataGenerator
from shared_code.app.reddit_data_collection import Collector

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


@click.group()
def cli4():
	pass


@cli1.command()
@click.option("--bot-names", prompt='specify the bot name. Must be present in the praw.ini file', default='')
@click.option("--sub-reddit", prompt='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+THE_Pablop+SubSimGPT2Interactive', default='CoopAndPabloPlayHouse')
@click.option("--reply-rate", prompt='The base rate at which a bot will randomly reply. random.int(0,N) / N', default='10')
def run_multi_bot(bot_names: str, sub_reddit: str, reply_rate: str):
	os.environ["ReplyThreshold"] = reply_rate
	bots = bot_names.split(",")
	BotRunner().run_multi_bot(bots, sub_reddit)


@cli2.command()
@click.option("--redditor",
			  prompt='The name of the redditor to collect data on',
			  default='generic')
def collect_data(redditor: str):
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	Collector().get_author_comments(redditor)


@cli3.command()
@click.option("--redditor",
			  prompt='The name of the redditor to collect data on',
			  default='generic')
def create_training(redditor: str):
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	TrainingDataGenerator().run(redditor.split(","))


@cli4.command()
@click.option("--threads", prompt='number of threads to run', default=1)
def run_message_processor(threads: int):
	BotRunner().run_process(thread_count=threads)


cli = click.CommandCollection(sources=[cli1, cli2, cli3, cli4])

if __name__ == '__main__':
	cli()
