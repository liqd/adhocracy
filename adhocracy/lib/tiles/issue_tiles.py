from util import render_tile, BaseTile
from webhelpers.text import truncate

from .. import text
from .. import helpers as h
from ..auth import authorization as auth
from .. import democracy

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class IssueTile(DelegateableTile):
    
    def __init__(self, issue):
        self.issue = issue
        self.__comment_tile = None
        DelegateableTile.__init__(self, issue)

    def _tagline(self):       
        if self.issue.comment and self.issue.comment.latest:
            tagline = text.plain(self.issue.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    can_edit = property(BaseTile.prop_has_perm('issue.edit'))
        
    def _can_delete(self):
        for proposal in self.issue.proposals:
            if not proposal.is_mutable():
                return False
        return h.has_permission("issue.delete")
    
    can_delete = property(_can_delete)
    can_create_proposal = property(BaseTile.prop_has_perm('proposal.create'))
    
    def _comment_tile(self):
        if not self.__comment_tile:
            self.__comment_tile = CommentTile(self.issue.comment)
        return self.__comment_tile
    
    comment_tile = property(_comment_tile)


def row(issue):
    return render_tile('/issue/tiles.html', 'row', IssueTile(issue), issue=issue, cached=True)


def header(issue, tile=None, active='goal'):
    if tile is None:
        tile = IssueTile(issue)
    return render_tile('/issue/tiles.html', 'header', tile, 
                       issue=issue, active=active)
