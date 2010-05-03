from util import render_tile, BaseTile

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _ 

from webhelpers.text import truncate

import adhocracy.model as model
from .. import helpers as h
from .. import text

class TextTile(BaseTile):
    
    def __init__(self, text):
        self.text = text 
        
    @property
    def parent_text_diff(self):
        if not self.text.parent:
            return self.text.render()
        return text.html_diff(self.text.parent.render(), 
                              self.text.render())
        
    @property 
    def parent_title_diff(self):
        if not self.text.parent:
            return self.text.title
        return text.html_diff(self.text.parent.title,
                              self.text.title)
                              
    index = 23                      
        
                              
def history_row(text):
    return render_tile('/text/tiles.html', 'history_row', 
                       TextTile(text), text=text)
    
    