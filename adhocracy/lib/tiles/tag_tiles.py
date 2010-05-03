from util import render_tile, BaseTile
from webhelpers.text import truncate

from .. import text
from .. import helpers as h
from ..auth import authorization as auth
from .. import democracy

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class TagTile(BaseTile):
    
    def __init__(self, tag):
        self.tag = tag


def row(tag):
    return render_tile('/tag/tiles.html', 'row', TagTile(tag), tag=tag, cached=True)


def cloud(tags, plain=True, show_count=False, link_more=True):
    from .. import templating 
    return templating.render_def('/tag/tiles.html', 'cloud', tags=tags, plain=plain, 
            show_count=show_count, link_more=link_more)
            
def sidebar(delegateable):
    from .. import templating 
    return templating.render_def('/tag/tiles.html', 'sidebar', delegateable=delegateable)