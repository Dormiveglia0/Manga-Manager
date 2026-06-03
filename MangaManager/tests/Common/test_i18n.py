import unittest
from unittest.mock import patch

from src.Common.i18n import FALLBACK_LANGUAGE, TRANSLATIONS, tr


class I18nTest(unittest.TestCase):
    def test_important_keys_exist_in_supported_languages(self):
        important_keys = [
            "button.open_files",
            "button.translate_tags",
            "settings.ui_language",
            "settings.tag_translation_rules",
            "message.nhentai_placeholder_body",
        ]
        for language in ("zh_CN", "en_US"):
            for key in important_keys:
                self.assertIn(key, TRANSLATIONS[language])

    def test_english_fallback_language_exists(self):
        self.assertIn(FALLBACK_LANGUAGE, TRANSLATIONS)

    def test_missing_localized_key_falls_back_to_english(self):
        with patch("src.Common.i18n.get_language", return_value="zh_CN"):
            with patch.dict(TRANSLATIONS["zh_CN"], {}, clear=True):
                with patch.dict(TRANSLATIONS["en_US"], {"fallback.only": "English"}, clear=True):
                    self.assertEqual(tr("fallback.only"), "English")


if __name__ == '__main__':
    unittest.main()
