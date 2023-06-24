import logging
import datetime
import os
import sys


class MinigalaxyLogFormatter(logging.Formatter):
    converter = datetime.date.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            logger.debug("Have date format")
            return ct.strftime(datefmt)
        else:
            time_string = ct.strftime("%Y-%m-%d %H:%M:%S")
            time_string_with_ms = "%s,%03d" % (time_string, record.msecs)
            return time_string_with_ms


# create logger for the minigalaxy application
logger = logging.getLogger('minigalaxy')
logger.setLevel(logging.DEBUG)

# The console should log DEBUG messages and up
ch = logging.StreamHandler(stream=sys.stdout)
debug = os.environ.get("MG_DEBUG")
if debug:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.ERROR)

# create formatter and add it to the handlers
# This doesn't use the MinigalaxyLogFormatter yet, it uses the default logging Formatter
formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(ch)
