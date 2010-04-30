from pylons import tmpl_context as c
from webhelpers.text import truncate

import adhocracy.model as model
from .. import text

from util import render_tile, BaseTile
from comment_tiles import CommentTile

class RevisionTile(BaseTile):
    
    def __init__(self, revision):
        self.revision = revision
        self.comment_tile = CommentTile(revision.comment)
    
    def _is_earliest(self):
        return self.revision == min(self.revision.comment.revisions, key=lambda r: r.create_time)
    
    is_earliest = property(_is_earliest)
    
    def _is_latest(self):
        return self.revision.comment.latest == self.revision
    
    is_latest = property(_is_latest)
    
    def _previous(self):
        if self.is_earliest:
            return None
        smaller = filter(lambda r: r.create_time < self.revision.create_time,
                         self.revision.comment.revisions)
        return max(smaller, key=lambda r: r.create_time)
        
    previous = property(_previous)
    
    def _diff_text(self):
        previous = self.previous
        if not previous:
            return text.render(self.revision.text)
        return text.html_diff(text.render(previous.text),
                              text.render(self.revision.text))
    
    diff_text = property(_diff_text)
    
    def _index(self):
        return len(self.revision.comment.revisions) - self.revision.comment.revisions.index(self.revision)
    
    index = property(_index)


def row(revision):
    return render_tile('/comment/revision_tiles.html', 'row', RevisionTile(revision), revision=revision)    

