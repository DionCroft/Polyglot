import json, re


class Glossary:
    """Exact term matching only; target corrections require the source term."""

    def __init__(self, path=None, vocabulary=""):
        self.entries = (
            json.loads(path.read_text(encoding="utf-8"))
            if path and path.is_file()
            else {}
        )
        self.vocabulary = [s.strip() for s in vocabulary.splitlines() if s.strip()][
            :100
        ]

    @staticmethod
    def pattern(term):
        return re.compile(r"(?<![\w])" + re.escape(term) + r"(?![\w])", re.I)

    def english(self, text):
        for canonical, entry in self.entries.items():
            for alias in entry.get("asr_aliases", []):
                text = self.pattern(alias).sub(lambda _, value=canonical: value, text)
        for word in self.vocabulary:
            text = self.pattern(word).sub(lambda _: word, text)
        return text

    def chinese(self, english, chinese):
        for canonical, entry in self.entries.items():
            terms = [
                canonical,
                entry.get("english", canonical),
                *entry.get("aliases", []),
            ]
            if not any(self.pattern(t).search(english) for t in terms):
                continue
            if any(english.strip(" .!?").casefold() == t.casefold() for t in terms):
                return entry["chinese"]
            for target in entry.get("target_aliases", []):
                chinese = chinese.replace(target, entry["chinese"])
            if canonical.isupper():
                chinese = self.pattern(canonical).sub(
                    lambda _: entry["chinese"] + f" ({canonical})", chinese
                )
        return chinese
