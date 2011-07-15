from adhocracy.lib.tiles.comment_tiles import CommentTile
from adhocracy.lib.tiles.util import render_tile, BaseTile


class RevisionTile(BaseTile):

    def __init__(self, revision):
        self.revision = revision
        self.comment_tile = CommentTile(revision.comment)


def row(revision):
    return render_tile('/comment/revision_tiles.html', 'row',
                       RevisionTile(revision), revision=revision)
