from util import render_tile, BaseTile

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _ 

from webhelpers.text import truncate

import adhocracy.model as model
from .. import helpers as h
from .. import text
from .. import sorting

class TextTile(BaseTile):
    
    def __init__(self, text):
        self.text = text 
    
     
def history_row(text):
    return render_tile('/text/tiles.html', 'history_row', 
                       TextTile(text), text=text)

    
def full(text, subpages_pager=None, hide_discussion=True):
    return render_tile('/text/tiles.html', 'full', 
                       TextTile(text), text=text, 
                       subpages_pager=subpages_pager,
                       hide_discussion=hide_discussion)

                       
def descbox(this, other, options=None, field=None):
    return render_tile('/text/tiles.html', 'descbox', TextTile(this),
                       this=this, other=other, options=options, field=field)
                       