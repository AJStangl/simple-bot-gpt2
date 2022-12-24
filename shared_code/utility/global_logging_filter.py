import logging
import re
class LoggingExtension(object):
	@staticmethod
	def set_global_logging_level(level=logging.ERROR, prefices=[""]):
		prefix_re = re.compile(fr'^(?:{ "|".join(prefices) })')
		for name in logging.root.manager.loggerDict:
			if re.match(prefix_re, name):
				logging.getLogger(name).setLevel(level)

	@staticmethod
	def get_logging_format() -> str:
		logging_format = f'|:: Thread:%(threadName)s %(levelname)s ::| %(message)s'
		return logging_format