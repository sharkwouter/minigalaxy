import logging
import os
import gettext
import locale
from minigalaxy.config import Config
from minigalaxy.paths import LOCALE_DIR

TRANSLATION_DOMAIN = "minigalaxy"
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    logging.error("Unsupported locale detected, continuing with available locale categories", exc_info=1)

# A formatting category (for example LC_TIME) may be unavailable even when
# LC_MESSAGES is valid. Initialize the message category independently.
try:
    locale.setlocale(locale.LC_MESSAGES, '')
except locale.Error:
    logging.error("Unsupported message locale, continuing with the current message locale", exc_info=1)

system_message_locale = locale.setlocale(locale.LC_MESSAGES)


def set_message_locale(language):
    """Apply a program language without changing formatting or character categories.

    The empty configuration value always restores the startup system language.
    """
    target = (language, 'UTF-8') if language else system_message_locale
    locale.setlocale(locale.LC_MESSAGES, target)


current_locale = Config().locale
try:
    set_message_locale(current_locale)
except locale.Error:
    logging.error("Configured program language is unavailable, using the system language", exc_info=1)
    set_message_locale('')
    current_locale = ''

try:
    locale.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
except AttributeError:
    logging.error("Couldn't run locale.bindtextdomain. Translations might not work correctly.", exc_info=1)

try:
    locale.textdomain(TRANSLATION_DOMAIN)
except AttributeError:
    logging.error("Couldn't run locale.textdomain. Translations might not work correctly.", exc_info=1)

gettext.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.textdomain(TRANSLATION_DOMAIN)

# LANGUAGE can override the explicit program language in native gettext.
# Keep LANG intact so games inherit the original system locale.
os.unsetenv("LANGUAGE")

default_locale = locale.getlocale(locale.LC_MESSAGES)[0]
logging.debug("Init locales: default=%s, current=%s", default_locale, current_locale)
logging.debug("Loading locale files from %s", LOCALE_DIR)
if current_locale == '':
    if default_locale is None:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=['en'], fallback=True)
    else:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[default_locale], fallback=True)
else:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[current_locale], fallback=True)
_ = lang.gettext
