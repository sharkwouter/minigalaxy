import gettext
import locale
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

gettext.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.textdomain(TRANSLATION_DOMAIN)
_ = gettext.gettext
gettext.install(TRANSLATION_DOMAIN, LOCALE_DIR)
