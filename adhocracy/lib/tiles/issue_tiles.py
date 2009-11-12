from util import render_tile, BaseTile
from webhelpers.text import truncate

from .. import text
from .. import helpers as h
from .. import authorization as auth
from .. import democracy

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class IssueTile(DelegateableTile):
    
    def __init__(self, issue):
        self.issue = issue
        self.__comment_tile = None
        DelegateableTile.__init__(self, issue)
        
    def _num_motions(self):
        return len(self.issue.motions)
    
    num_motions = property(_num_motions)
    
    def _tagline(self):       
        if self.issue.comment and self.issue.comment.latest:
            tagline = text.plain(self.issue.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    can_edit = property(DelegateableTile.prop_has_permkarma('issue.edit'))
    lack_edit_karma = property(BaseTile.prop_lack_karma('issue.edit'))   
        
    def _can_delete(self):
        for motion in self.issue.motions:
            state = democracy.State(motion)
            if not state.motion_mutable:
                return False
        return auth.on_delegateable(self.issue, "issue.delete",
                                    allow_creator=False if len(self.issue.motions) else True)
    
    can_delete = property(_can_delete)
    lack_delete_karma = property(BaseTile.prop_lack_karma('issue.delete'))
    
    can_create_motion = property(DelegateableTile.prop_has_permkarma('motion.create', allow_creator=False))
    lack_create_motion_karma = property(BaseTile.prop_lack_karma('motion.create'))
    
    def _comment_tile(self):
        if not self.__comment_tile:
            self.__comment_tile = CommentTile(self.issue.comment)
        return self.__comment_tile
    
    comment_tile = property(_comment_tile)
        

def row(issue):
    return render_tile('/issue/tiles.html', 'row', IssueTile(issue), issue=issue)
