import os
import gettext
import locale
from minigalaxy.config import Config
from minigalaxy.logger import logger
from minigalaxy.paths import LOCALE_DIR

TRANSLATION_DOMAIN = "minigalaxy"
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    logger.error("Unsupported locale detected, continuing without translation support", exc_info=1)

try:
    locale.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
except AttributeError:
    logger.error("Couldn't run locale.bindtextdomain. Translations might not work correctly.", exc_info=1)

try:
    locale.textdomain(TRANSLATION_DOMAIN)
except AttributeError:
    logger.error("Couldn't run locale.textdomain. Translations might not work correctly.", exc_info=1)

gettext.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.textdomain(TRANSLATION_DOMAIN)

# Make sure LANGUAGE and LANG are not set, or translations will not be loaded
os.unsetenv("LANGUAGE")
os.unsetenv("LANG")

current_locale = Config().locale
default_locale = locale.getdefaultlocale()[0]
if current_locale == '':
    if default_locale is None:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=['en'], fallback=True)
    else:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[default_locale], fallback=True)
else:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[current_locale], fallback=True)
_ = lang.gettext
