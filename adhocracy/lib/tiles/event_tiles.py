from util import render_tile

from pylons import tmpl_context as c
from webhelpers.text import truncate
from ..event import formatting 
from ..text import meta_escape

class EventTile():
    
    def __init__(self, event):
        self.event = event
        self._text = None
        
    def _get_text(self):
        if self._text is None:
           self._text = self.event.text()
           if self._text is not None:
               self._text = meta_escape(self._text)
               self._text = truncate(self._text, length=160, 
                                     indicator="...", whole_word=True)
        return self._text
    
    text = property(_get_text)

    
def row(event):
    return render_tile('/event/tiles.html', 'row', 
                       EventTile(event), event=event, cached=True)