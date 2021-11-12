import os
import gettext
import locale
from minigalaxy.config import Config
from minigalaxy.paths import LOCALE_DIR

TRANSLATION_DOMAIN = "minigalaxy"
USING_LANGUAGE_ENV_VAR = False
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

# Handle LANGUAGE env variable similarly to how the UI interprets it
languages = os.environ.get("LANGUAGE")
language_locale = None
if languages:
    USING_LANGUAGE_ENV_VAR = True
    supported_locales = os.listdir(LOCALE_DIR)
    for language in languages.split(':'):
        if 'en' not in language and language in supported_locales:
            language_locale = language.split('_')[0]
            break

current_locale = Config.get("locale")
default_locale = locale.getdefaultlocale()[0]
if language_locale:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[language_locale], fallback=True)
elif languages or current_locale == '' and default_locale is None:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=['en'], fallback=True)
elif current_locale == '':
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[default_locale], fallback=True)
else:
    lang = gettext.translation(TRANSLATION_DOMAIN, LOCALE_DIR, languages=[current_locale], fallback=True)
_ = lang.gettext
