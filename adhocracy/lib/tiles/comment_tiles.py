from pylons import tmpl_context as c
from webhelpers.text import truncate

import adhocracy.model as model
from .. import text
from ..auth import authorization as auth
from .. import democracy
from .. import sorting
from .. import helpers as h
from .. import cache
from .. import text 

from util import render_tile, BaseTile

class CommentTile(BaseTile):
    
    def __init__(self, comment):
        self.comment = comment
        self.__topic_outbound = None 
        self.__score = None
    
    
    @property    
    def text(self):       
        if self.comment and self.comment.latest:
            return text.render(self.comment.latest.text)
        return ""
    
    
    @property
    def tagline(self):       
        if self.comment.latest:
            tagline = text.plain(self.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    
    @property
    def on_proposal(self):
        return isinstance(self.comment.topic, model.Proposal)
    
    
    @property
    def is_own(self):
        return self.comment.creator == c.user
    
    
    @property
    def show(self):
        if self.comment.is_deleted():
            children = map(lambda c: CommentTile(c)._show(), self.comment.replies) 
            if not True in children:
                return False
        return True
        
    
    @property
    def num_children(self):
        num = len(filter(lambda c: not c.delete_time, self.comment.replies))
        num += sum(map(lambda c: CommentTile(c)._num_children(), self.comment.replies))
        return num
    
    
    @property
    def score(self):
        return self.comment.poll.tally.score
    
    
    @property
    def position(self):
        @cache.memoize('comment_position')
        def _cached_position(user, comment):
            if not user:
                return None
            pos = democracy.Decision(user, comment.poll).result
            if (pos and pos == 1):
                return "upvoted"
            elif pos and pos == -1:
                return "downvoted"
            return pos
            
        return _cached_position(c.user, self.comment)
    
    
    def replies(self):
        comments = sorting.comment_order(self.comment.replies)
        for comment in comments:
            tile = self.__class__(comment)
            tile.__topic_outbound = self.__topic_outbound
            yield (comment, tile)


def row(comment):
    return render_tile('/comment/tiles.html', 'row', CommentTile(comment), comment=comment)    


def header(comment, tile=None, active='comment'):
    if tile is None:
        tile = CommentTile(comment)
    return render_tile('/comment/tiles.html', 'header', tile, 
                       comment=comment, active=active)


def full(comment, recurse=True, collapse=False, link_discussion=False):
    return render_tile('/comment/tiles.html', 'full', CommentTile(comment), 
                       recurse=recurse, comment=comment, collapse=collapse, 
                       link_discussion=link_discussion, cached=False)

