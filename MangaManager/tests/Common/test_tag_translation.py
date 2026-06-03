import unittest

from src.Common.tag_translation import parse_tag_translation_rules, translate_tags


class TagTranslationTest(unittest.TestCase):
    def test_exact_match_translation(self):
        self.assertEqual(translate_tags("full color, sole male", "full color=全彩\nsole male=单男主"), "全彩, 单男主")

    def test_strips_spaces_for_matching(self):
        self.assertEqual(translate_tags(" full color , unmatched ", "full color=全彩"), "全彩, unmatched")

    def test_unmatched_tags_are_preserved(self):
        self.assertEqual(translate_tags("full color, comedy", "full color=全彩"), "全彩, comedy")

    def test_duplicate_tags_are_preserved(self):
        self.assertEqual(translate_tags("full color, full color", "full color=全彩"), "全彩, 全彩")

    def test_empty_rules_keep_original_value(self):
        self.assertEqual(translate_tags("full color", ""), "full color")

    def test_invalid_rule_lines_are_ignored(self):
        self.assertEqual(parse_tag_translation_rules("bad line\nfull color=全彩"), {"full color": "全彩"})

    def test_conflict_value_is_not_translated(self):
        self.assertEqual(translate_tags("~~conflict~~", "~~conflict~~=转换", "~~conflict~~"), "~~conflict~~")


if __name__ == '__main__':
    unittest.main()
