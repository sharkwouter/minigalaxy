import logging
import datetime

class MinigalaxyLogFormatter(logging.Formatter):
    converter = datetime.date.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            print("Have date format\n")
            return ct.strftime(datefmt)
        else:
            time_string = ct.strftime("%Y-%m-%d %H:%M:%S")
            time_string_with_ms = "%s,%03d" % (t, record.msecs)
            return time_string_with_ms

# create logger for the minigalaxy application
logger = logging.getLogger('minigalaxy')
logger.setLevel(logging.DEBUG)

# The console should log DEBUG messages and up
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# create formatter and add it to the handlers
formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(ch)
