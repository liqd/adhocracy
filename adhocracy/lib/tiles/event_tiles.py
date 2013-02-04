from util import render_tile

from webhelpers.text import truncate
from adhocracy.lib.text import markdown_to_plain_text


class EventTile():

    def __init__(self, event):
        self.event = event
        self._text = None

    def _get_text(self):
        if self._text is None:
            text = markdown_to_plain_text(self.event.text(), safe_mode='remove')
            self._text = truncate(text, length=160,
                                  indicator="...", whole_word=True)
        return self._text

    text = property(_get_text)


def row(event):
    return render_tile('/event/tiles.html', 'row',
                       EventTile(event), event=event, cached=True)
