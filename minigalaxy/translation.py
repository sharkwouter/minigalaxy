import gettext
import locale
from minigalaxy.paths import LOCALE_DIR

TRANSLATION_DOMAIN = "minigalaxy"

locale.setlocale(locale.LC_ALL, '')
locale.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.bindtextdomain(TRANSLATION_DOMAIN, LOCALE_DIR)
gettext.textdomain(TRANSLATION_DOMAIN)
_ = gettext.gettext
gettext.install(TRANSLATION_DOMAIN, LOCALE_DIR)
