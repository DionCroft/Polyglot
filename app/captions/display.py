"""Caption handover state independent of Qt, suitable for deterministic tests."""


class CaptionDisplay:
    def __init__(self):
        self.pair = None
        self.pending = None
        self.partial = None
        self.epoch = -1
        self.rejected_through = -1

    def reject_partial(self, identifier, epoch):
        """Retract an uncertain provisional phrase without losing a completed pair."""
        if epoch != self.epoch:
            return
        self.rejected_through = max(self.rejected_through, identifier)
        if self.partial and self.partial.identifier <= identifier:
            self.partial = None

    def accept(self, caption):
        if caption.epoch < self.epoch:
            return False
        if caption.epoch > self.epoch:
            self.__init__()
            self.epoch = caption.epoch
        if caption.final and (
            caption.translated_text or caption.translation_status == "unavailable"
        ):
            if self.pair and caption.identifier <= self.pair.identifier:
                return False
            self.pair = caption
            if self.pending and self.pending.identifier <= caption.identifier:
                self.pending = None
            if self.partial and self.partial.identifier <= caption.identifier:
                self.partial = None
        elif caption.final:
            if self.pair and caption.identifier <= self.pair.identifier:
                return False
            if self.pending and caption.identifier <= self.pending.identifier:
                return False
            self.pending = caption
            if self.partial and self.partial.identifier <= caption.identifier:
                self.partial = None
        else:
            if caption.identifier <= self.rejected_through:
                return False
            boundary = max(
                self.pair.identifier if self.pair else -1,
                self.pending.identifier if self.pending else -1,
            )
            if caption.identifier <= boundary:
                return False
            if self.partial and caption.identifier < self.partial.identifier:
                return False
            self.partial = caption
        return True

    def contents(self, mode="Bilingual"):
        latest = self.pending or self.pair or self.partial
        if mode == "English":
            latest = self.partial or latest
            return (latest.english if latest else "", "", "")
        primary = self.pair or self.pending or self.partial
        en = primary.english if primary else ""
        zh = primary.chinese if primary else ""
        upcoming = self.partial or self.pending
        extra = (
            upcoming.source_text
            if upcoming and primary and upcoming.identifier > primary.identifier
            else ""
        )
        return en, zh, extra

    def primary(self, mode="Bilingual"):
        """The caption whose text is currently visible, even while another turn loads."""
        if mode == "English":
            return self.partial or self.pending or self.pair
        return self.pair or self.pending or self.partial
