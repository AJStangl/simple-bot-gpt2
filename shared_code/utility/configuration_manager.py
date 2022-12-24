import os, configparser
class ConfigurationManager(object):
	def __init__(self):
		config: configparser.ConfigParser = configparser.ConfigParser()
		config.optionxform = str
		config.read('config.ini', encoding='utf-8')
		sections = config.sections()
		for sections in sections:
			for key, value in config.items(sections):
				# print(f"Setting Key: {key}: With Value {value} to environment")
				os.environ[key] = value
