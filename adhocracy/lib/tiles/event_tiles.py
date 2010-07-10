from util import render_tile

from pylons import tmpl_context as c
from webhelpers.text import truncate
from ..event import formatting 
from ..text import plain_html

class EventTile():
    
    def __init__(self, event):
        self.event = event
        self._text = None
        
    def _get_text(self):
        if self._text is None:
            text = plain_html(self.event.text())
            self._text = truncate(text, length=160, 
                                  indicator="...", whole_word=True)
        return self._text
    
    text = property(_get_text)

    
def row(event):
    return render_tile('/event/tiles.html', 'row', 
                       EventTile(event), event=event, cached=True)