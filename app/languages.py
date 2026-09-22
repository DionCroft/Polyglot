"""Explicit conversation directions; codes remain stable in settings and journals."""

LANGUAGES = {"en": "English", "zh": "Mandarin Chinese"}
DIRECTIONS = {"en": "English → 简体中文", "zh": "普通话 → English"}


def validate_language(language):
    if language not in LANGUAGES:
        raise ValueError("Choose English or Mandarin Chinese.")
    return language


def caption_labels(language):
    return (
        ("English · spoken", "简体中文 · translation")
        if language == "en"
        else ("English · translation", "简体中文 · spoken")
    )
