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


def row(revision):
    return render_tile('/comment/revision_tiles.html', 'row', RevisionTile(revision), revision=revision)    

