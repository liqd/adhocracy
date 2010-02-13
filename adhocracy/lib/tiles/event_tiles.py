from util import render_tile

from pylons import tmpl_context as c
from ..event import formatting 

class EventTile():
    
    def __init__(self, event):
        self.event = event
    
def row(event):
    return render_tile('/event/tiles.html', 'row', 
                       EventTile(event), event=event, cached=True)