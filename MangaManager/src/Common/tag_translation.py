from __future__ import annotations

import logging

logger = logging.getLogger("TagTranslation")


def parse_tag_translation_rules(rules_text: str | None) -> dict[str, str]:
    rules = {}
    if not rules_text:
        return rules

    for line_no, line in enumerate(rules_text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if "=" not in line:
            logger.warning("Ignoring invalid tag translation rule at line %s: %s", line_no, line)
            continue
        source, target = line.split("=", 1)
        source = source.strip()
        target = target.strip()
        if not source:
            logger.warning("Ignoring tag translation rule with empty source at line %s", line_no)
            continue
        rules[source] = target
    return rules


def translate_tags(tags_value: str | None, rules_text: str | None, conflict_value: str | None = None) -> str:
    if tags_value is None:
        return ""
    if conflict_value is not None and tags_value == conflict_value:
        return tags_value
    if tags_value.strip() == "":
        return tags_value

    rules = parse_tag_translation_rules(rules_text)
    if not rules:
        return tags_value

    translated_tags = []
    for tag in tags_value.split(","):
        stripped_tag = tag.strip()
        if stripped_tag in rules:
            translated_tags.append(rules[stripped_tag])
        else:
            translated_tags.append(stripped_tag)
    return ", ".join(translated_tags)
