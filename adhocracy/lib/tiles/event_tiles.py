from util import render_tile

from pylons import tmpl_context as c
from ..event import formatting 

class EventTile():
    
    def __init__(self, event):
        self.event = event
    

def list_item(event):
    event_html = formatting.as_html(event)
    return render_tile('/event/tiles.html', 'list_item', 
                       EventTile(event), event=event, event_html=event_html)