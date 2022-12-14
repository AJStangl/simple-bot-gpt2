from setuptools import setup
import os


def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
	name="simple-bot-gpt2",
	version="0.0.1",
	author="AJ Stangl",
	author_email="ajstangl@gmail.com",
	description="A simple wrapper for collecting, transforming, and creating gpt2 models based on reddit users/subreddits",
	license="MIT",
	keywords="GPT2",
	include_package_data=True,
	url="https://example.com",
	packages=['shared_code',
			  'shared_code/app',
			  'shared_code/bot',
			  'shared_code/clients',
			  'shared_code/fine_tuning',
			  'shared_code/fine_tuning/persistence',
			  'shared_code/fine_tuning/tensor_encoding',
			  'shared_code/handlers',
			  'shared_code/models',
			  'shared_code/process',
			  'shared_code/tagging',
			  'shared_code/messaging',
			  'shared_code/text_generation',
			  'shared_code/text_generation/text',
			  'shared_code/text_generation/toxicity',
			  'shared_code/utility'],

	long_description=read('README.md'),
	classifiers=[
		"Topic :: Utilities",
		"License :: MIT License",
	],
	entry_points={
		'console_scripts': [
			'simple-bot-gpt2 = shared_code.cli_wrapper:cli',
		],
	},
)
