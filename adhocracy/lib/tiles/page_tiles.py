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
from .. import sorting

class PageTile(BaseTile):
    
    def __init__(self, page):
        self.page = page
        
    
    def _can_edit(self):
        return h.has_permission('page.edit')

    can_edit = property(_can_edit)    


    def _can_delete(self):
        return h.has_permission('page.delete')

    can_delete = property(_can_delete)
    
    def comments(self):
        from comment_tiles import CommentTile
        comments = sorting.comment_order(self.page.comments)
        for comment in comments:
            if comment.reply: 
                continue
            tile = CommentTile(comment)
            yield (comment, tile)


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
 