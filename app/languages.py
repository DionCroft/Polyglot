"""Explicit conversation directions; codes remain stable in settings and journals."""

LANGUAGES = {"en": "English", "zh": "Mandarin Chinese"}
DIRECTIONS = {
    "en": "English → 简体中文",
    "zh": "普通话 → English",
    "auto": "Auto · English ↔ 普通话",
}


def validate_language(language):
    if language not in LANGUAGES:
        raise ValueError("Choose English or Mandarin Chinese.")
    return language


def validate_selection(language):
    if language not in DIRECTIONS:
        raise ValueError("Choose English, Mandarin Chinese or Auto.")
    return language


def caption_labels(language):
    if language == "auto":
        return "English", "简体中文"
    return (
        ("English · spoken", "简体中文 · translation")
        if language == "en"
        else ("English · translation", "简体中文 · spoken")
    )
