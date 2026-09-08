from app.captions.state import Caption


class CaptionStabiliser:
    """Only VAD-final phrases are committed/translated; provisional text never is."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.last_final = -1

    def accept(self, phrase, text, epoch=0):
        text = " ".join(text.split())
        if not text or phrase.identifier <= self.last_final:
            return None
        if phrase.final:
            self.last_final = phrase.identifier
        return Caption(
            phrase.identifier,
            phrase.start,
            phrase.end,
            text,
            final=phrase.final,
            epoch=epoch,
        )
