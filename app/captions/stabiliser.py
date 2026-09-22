from app.captions.state import Caption


class CaptionStabiliser:
    """Only VAD-final phrases are committed/translated; provisional text never is."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.last_final = -1
        self.current = None
        self.previous = []
        self.stable = []

    def accept(self, phrase, text, epoch=0, source_language="en"):
        text = " ".join(text.split())
        if not text or phrase.identifier <= self.last_final:
            return None
        if self.current != (epoch, phrase.identifier):
            self.current = (epoch, phrase.identifier)
            self.previous = []
            self.stable = []
        # Chinese has no mandatory word spaces. Compare characters for stable prefixes.
        words = list(text) if source_language == "zh" else text.split()
        if phrase.final:
            self.last_final = phrase.identifier
        else:
            common = []
            for old, new in zip(self.previous, words):
                if old.casefold().strip(".,!?") != new.casefold().strip(".,!?"):
                    break
                common.append(new)
            self.previous = words
            if len(common) > len(self.stable):
                self.stable = common
            # Wait for agreement from two hypotheses before displaying a prefix.
            if not self.stable:
                return None
            text = ("" if source_language == "zh" else " ").join(self.stable)
        return Caption(
            phrase.identifier,
            phrase.start,
            phrase.end,
            text if source_language == "en" else "",
            chinese=text if source_language == "zh" else "",
            final=phrase.final,
            epoch=epoch,
            source_language=source_language,
        )
