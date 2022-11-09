import logging
import os
import time


import click
from dotenv import load_dotenv

from shared_code.app.generate_training_data import TrainingDataGenerator
from shared_code.app.reddit_data_collection import Collector
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

@click.group()
def cli4():
	pass



@cli1.command()
@click.option("--bot-name", prompt='specify the bot name. Must be present in the praw.ini file', default='')
@click.option("--sub-reddit", prompt='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+THE_Pablop+SubSimGPT2Interactive', default='CoopAndPabloPlayHouse')
@click.option("--reply-rate", prompt='The base rate at which a bot will randomly reply. N / 1000', default='900')
def run_bot(bot_name: str, sub_reddit: str, reply_rate: str):
	os.environ["ReplyThreshold"] = reply_rate
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{bot_name}|{sub_reddit}|::| %(message)s', level=logging.INFO)
	logging.info(f"Setting Random Reply To {reply_rate}")
	bot = RedditBot(bot_name, sub_reddit)
	bot.name = bot_name
	bot.daemon = True
	bot.run()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info('Shutdown')
		bot.stop()


@cli2.command()
@click.option("--redditor", prompt='The name of the redditor to collect data on', default='generic')
def collect_data(redditor: str):
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	Collector().get_author_comments(redditor)


@cli3.command()
@click.option("--redditor", prompt='The name of the redditor to collect data on', default='generic')
def create_training(redditor: str):
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	TrainingDataGenerator().run(redditor.split(","))


@cli4.command()
@click.option("--bot-names", prompt='specify the bot name. Must be present in the praw.ini file', default='')
@click.option("--sub-reddit", prompt='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse+THE_Pablop+SubSimGPT2Interactive', default='CoopAndPabloPlayHouse')
@click.option("--reply-rate", prompt='The base rate at which a bot will randomly reply. N / 1000', default='900')
def run_multi_bot(bot_names: str, sub_reddit: str, reply_rate: str):
	os.environ["ReplyThreshold"] = reply_rate
	logging.basicConfig(format=f'|:: Thread:%(threadName)s %(asctime)s %(levelname)s ::| %(message)s', level=logging.INFO)
	logging.info(f"Setting Random Reply To {reply_rate}")
	bots = []
	for bot_name in bot_names.split(","):
		bot = RedditBot(bot_name, sub_reddit)
		bots.append(bot)
		bot.name = bot_name
		bot.daemon = True
		bot.run()
	try:
		while True:
			time.sleep(5)
	except KeyboardInterrupt:
		logging.info('Shutdown')
		map(lambda x: x.stop(), bots)
		exit(0)


cli = click.CommandCollection(sources=[cli1, cli2, cli3, cli4])

if __name__ == '__main__':
	cli()
