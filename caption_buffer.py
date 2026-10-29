"""In-memory caption assembly for live partials and optional monologue accumulate."""

MAX_CHARS = 4000


class CaptionBuffer:
    """Keeps committed finals and a replaceable pending partial in RAM only."""

    def __init__(self, max_chars=MAX_CHARS):
        self.max_chars = max_chars
        self.committed = ''
        self.pending = ''

    def clear(self):
        self.committed = ''
        self.pending = ''

    def display(self):
        parts = [part for part in (self.committed, self.pending) if part]
        return ' '.join(parts)

    def _trim(self):
        text = self.display()
        if len(text) <= self.max_chars:
            return
        # Keep the newest end of the monologue in RAM.
        overflow = len(text) - self.max_chars
        if len(self.committed) <= overflow:
            self.committed = ''
            self.pending = self.pending[-(self.max_chars):]
        else:
            self.committed = self.committed[overflow:].lstrip()

    def update(self, text, final, accumulate):
        text = (text or '').strip()
        if not text:
            return self.display()
        if not accumulate:
            self.committed = ''
            self.pending = ''
            if final:
                self.committed = text
            else:
                self.pending = text
            self._trim()
            return self.display()
        if final:
            self.committed = f'{self.committed} {text}'.strip() if self.committed else text
            self.pending = ''
        else:
            self.pending = text
        self._trim()
        return self.display()
