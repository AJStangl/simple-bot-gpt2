import logging

import click
from dotenv import load_dotenv
from shared_code.utility.configuration_manager import ConfigurationManager

ConfigurationManager()
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


@click.group()
def cli5():
	pass


@click.group()
def cli6():
	pass


@cli1.command()
@click.option("-b", "--bot-names", help='specify the bot name. Must be present in the praw.ini file',
			  default='KimmieBotGPT,SportsFanBotGhostGPT,LauraBotGPT,NickBotGPT,DougBotGPT,AlbertBotGPT,SteveBotGPT',
			  show_default=True, required=True)
@click.option("-s", "--sub-reddit",
			  help='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse',
			  default='CoopAndPabloPlayHouse', show_default=True, required=True)
def run_bot_process(bot_names: str, sub_reddit: str):
	from shared_code.app.bot_runner import BotRunner
	bots = bot_names.split(",")
	BotRunner().run_bots(bots, sub_reddit)


@cli2.command()
@click.option("-t", "--threads", help='number of threads to run', default=1)
def run_reply_process(threads: int):
	from shared_code.app.bot_runner import BotRunner
	BotRunner().run_process(thread_count=threads)


@cli3.command()
@click.option("-b", "--bot-names", help='specify the bot name. Must be present in the praw.ini file',
			  default='KimmieBotGPT,SportsFanBotGhostGPT,LauraBotGPT,NickBotGPT,DougBotGPT,AlbertBotGPT,SteveBotGPT',
			  show_default=True, required=True)
@click.option("-s", "--sub-reddit",
			  help='specify the sub-reddit name(s). Example. CoopAndPabloPlayHouse',
			  default='CoopAndPabloPlayHouse', show_default=True, required=True)
@click.option("-t", "--threads", help='number of threads to run', default=6, show_default=True, required=True)
def run_all(bot_names: str, sub_reddit: str, threads: int):
	from shared_code.app.bot_runner import BotRunner
	BotRunner().run_all(bot_names, sub_reddit, threads)


@cli5.command()
@click.option("-r", "--redditor", help='The name of the redditor to collect data on', required=True)
def collect_data(redditor: str):
	from shared_code.app.reddit_data_collection import Collector
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	Collector().get_author_comments(redditor)


@cli6.command()
@click.option("-r", "--redditor", help='The name of the redditor to collect data on', required=True)
def create_training(redditor: str):
	from shared_code.app.generate_training_data import TrainingDataGenerator
	logging.basicConfig(format=f'|:: Thread:%(thread)s|%(asctime)s|{redditor}|::| %(message)s', level=logging.INFO)
	TrainingDataGenerator().run(redditor.split(","))


cli = click.CommandCollection(sources=[cli1, cli2, cli3, cli4, cli5, cli6])

if __name__ == '__main__':
	cli()
