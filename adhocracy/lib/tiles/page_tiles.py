from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate
import adhocracy.model as model

import proposal_tiles
import comment_tiles

from .. import democracy
from .. import helpers as h
from .. import text

from delegateable_tiles import DelegateableTile

class PageTile(DelegateableTile):
    
    def __init__(self, page):
        self.page = page
        DelegateableTile.__init__(self, page)
    
    


def row(page):
    return render_tile('/page/tiles.html', 'row', PageTile(page), 
                       page=page, cached=True)  


def header(page, tile=None, active='goal', text=None):
    if tile is None:
        tile = PageTile(page)
    if text is None:
        text = page.head
    return render_tile('/page/tiles.html', 'header', tile, 
                       page=page, text=text, active=active)
 