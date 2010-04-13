from pylons import tmpl_context as c
from webhelpers.text import truncate

import adhocracy.model as model
from .. import text
from ..auth import authorization as auth
from .. import democracy
from .. import sorting
from .. import helpers as h
from .. import cache

from util import render_tile, BaseTile

class CommentTile(BaseTile):
    
    def __init__(self, comment):
        self.comment = comment
        self.__topic_outbound = None 
        self.__score = None
        
    def _text(self):       
        if self.comment and self.comment.latest:
            return text.render(self.comment.latest.text)
        return ""
    
    text = property(_text)
    
    def _tagline(self):       
        if self.comment.latest:
            tagline = text.plain(self.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _on_proposal(self):
        return isinstance(self.comment.topic, model.Proposal)
    
    on_proposal = property(_on_proposal)
    
    def _on_issue(self):
        return isinstance(self.comment.topic, model.Issue)
    
    on_issue = property(_on_issue)
    
    def _is_own(self):
        return self.comment.creator == c.user
    
    is_own = property(_is_own)
    
    def _show(self):
        if self.comment.is_deleted():
            children = map(lambda c: CommentTile(c)._show(), self.comment.replies) 
            if not True in children:
                return False
        return True
    
    show = property(_show)
    
    def _num_children(self):
        num = len(filter(lambda c: not c.delete_time, self.comment.replies))
        num += sum(map(lambda c: CommentTile(c)._num_children(), self.comment.replies))
        return num
    
    num_children = property(_num_children)
    
    def _score(self):
        return self.comment.poll.tally.score
    
    score = property(_score)
    
    def _position(self):
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
    
    position = property(_position)
    
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

