import os
import gettext
import locale
from minigalaxy.config import Config
from minigalaxy.paths import LOCALE_DIR

TRANSLATION_DOMAIN = "minigalaxy"
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    print("Unsupported locale detected, continuing without translation support")

try:
    locale.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
except AttributeError:
    print("Couldn't run locale.bindtextdomain. Translations might not work correctly.")

try:
    locale.textdomain(TRANSLATION_DOMAIN)
except AttributeError:
    print("Couldn't run locale.textdomain. Translations might not work correctly.")

gettext.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.textdomain(TRANSLATION_DOMAIN)

# Make sure LANGUAGE and LANG are not set, or translations will not be loaded
os.unsetenv("LANGUAGE")
os.unsetenv("LANG")

current_locale = Config.get("locale")
default_locale = locale.getdefaultlocale()[0]
if current_locale == '':
    if default_locale is None:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=['en'], fallback=True)
    else:
        lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[default_locale], fallback=True)
else:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[current_locale], fallback=True)
_ = lang.gettext
