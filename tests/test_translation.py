import gettext
import locale
import runpy
from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import call, patch


class TestTranslation(TestCase):
    @contextmanager
    def load_translation(self, language='', message_language='en_US', setlocale_effect=None):
        # Execute an isolated module namespace: never replace the live translator
        # imported by the rest of the suite or mutate the runner's locale/env.
        with patch('locale.setlocale', return_value='en_US.UTF-8', side_effect=setlocale_effect) as setlocale, \
                patch('locale.getlocale', return_value=(message_language, 'UTF-8')) as getlocale, \
                patch('locale.bindtextdomain', create=True), patch('locale.textdomain', create=True), \
                patch('gettext.bindtextdomain'), patch('gettext.textdomain'), \
                patch('minigalaxy.config.Config') as config, \
                patch('gettext.translation', return_value=gettext.NullTranslations()) as translation, \
                patch('os.unsetenv') as unsetenv, patch('logging.error'):
            config.return_value.locale = language
            getlocale.side_effect = lambda category=locale.LC_CTYPE: (
                message_language if category == locale.LC_MESSAGES else 'de_DE', 'UTF-8')
            module = runpy.run_path('minigalaxy/translation.py')
            yield module, setlocale, translation, unsetenv

    def test_message_language_is_independent_of_character_locale(self):
        for message_language in ('en_US', 'fr_FR', None):
            with self.subTest(message_language=message_language):
                with self.load_translation(message_language=message_language) as (_, _, translation, _):
                    self.assertEqual(translation.call_args.kwargs['languages'], [message_language or 'en'])

    def test_unavailable_formatting_locale_does_not_block_messages(self):
        def setlocale(category, value=None):
            if category == locale.LC_ALL:
                raise locale.Error('unavailable LC_TIME')
            return 'en_US.UTF-8'

        with self.load_translation(setlocale_effect=setlocale) as (_, setter, translation, _):
            self.assertIn(call(locale.LC_MESSAGES, ''), setter.call_args_list)
            self.assertEqual(translation.call_args.kwargs['languages'], ['en_US'])

    def test_configured_language_applies_to_native_and_python_gettext(self):
        with self.load_translation(language='fr_FR') as (_, setter, translation, _):
            self.assertIn(call(locale.LC_MESSAGES, ('fr_FR', 'UTF-8')), setter.call_args_list)
            self.assertEqual(translation.call_args.kwargs['languages'], ['fr_FR'])

    def test_unavailable_configured_language_falls_back_to_system(self):
        def setlocale(category, value=None):
            if value == ('missing', 'UTF-8'):
                raise locale.Error('unavailable program language')
            return 'en_US.UTF-8'

        with self.load_translation(language='missing', setlocale_effect=setlocale) as (_, setter, translation, _):
            self.assertEqual(setter.call_args, call(locale.LC_MESSAGES, 'en_US.UTF-8'))
            self.assertEqual(translation.call_args.kwargs['languages'], ['en_US'])

    def test_restoring_system_language_preserves_other_categories(self):
        with self.load_translation() as (module, setter, _, _):
            setter.reset_mock()
            module['set_message_locale']('fr_FR')
            module['set_message_locale']('')
            self.assertEqual(setter.call_args_list, [
                call(locale.LC_MESSAGES, ('fr_FR', 'UTF-8')),
                call(locale.LC_MESSAGES, 'en_US.UTF-8'),
            ])

    def test_lang_is_retained_for_launched_games(self):
        with self.load_translation() as (_, _, _, unsetenv):
            self.assertNotIn(call('LANG'), unsetenv.call_args_list)
