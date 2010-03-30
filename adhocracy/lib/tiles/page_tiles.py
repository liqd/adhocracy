from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate
import adhocracy.model as model

import issue_tiles
import proposal_tiles
import comment_tiles

from .. import democracy
from .. import helpers as h
from .. import text

class PageTile(BaseTile):
    
    def __init__(self, page):
        self.page = page
        
    
    def _can_edit(self):
        return h.has_permission('page.edit')

    can_edit = property(_can_edit)    


    def _can_delete(self):
        return h.has_permission('page.delete')

    can_delete = property(_can_delete)



def row(page):
    return render_tile('/page/tiles.html', 'row', PageTile(page), 
                       page=page, cached=True)  


def header(page, tile=None, active='goal'):
    if tile is None:
        tile = PageTile(page)
    return render_tile('/page/tiles.html', 'header', tile, 
                       page=page, active=active)
 