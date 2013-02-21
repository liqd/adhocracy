from pylons import tmpl_context as c

from adhocracy.lib import text
from adhocracy.lib.auth import can
from adhocracy.lib.tiles.util import render_tile, BaseTile


class CommentTile(BaseTile):

    def __init__(self, comment):
        self.comment = comment
        self.__topic_outbound = None
        self.__score = None
        self.__num_child = None

    @property
    def text(self):
        if self.comment and self.comment.latest:
            return text.render(self.comment.latest.text)
        return ""

    @property
    def show(self):
        if self.comment.is_deleted():
            children = map(lambda c: CommentTile(c).show, self.comment.replies)
            if not True in children:
                return False
        return True

    @property
    def num_children(self):
        if self.__num_child is None:
            num = len(filter(
                lambda c: not c.delete_time, self.comment.replies))
            num += sum(map(lambda c: CommentTile(c).num_children,
                           self.comment.replies))
            self.__num_child = num
        return self.__num_child

    @property
    def score(self):
        return self.comment.poll.tally.score

    @property
    def is_low(self):
        return self.score <= -1


def row(comment):
    return render_tile('/comment/tiles.html', 'row', CommentTile(comment),
                       comment=comment)


def header(comment, tile=None, active='comment'):
    if tile is None:
        tile = CommentTile(comment)
    return render_tile('/comment/tiles.html', 'header', tile,
                       comment=comment, active=active)


def list(topic, root=None, comments=None, variant=None, recurse=True,
         ret_url=''):
    cached = True if c.user is None else False
    if comments is None:
        comments = topic.comments
    return render_tile('/comment/tiles.html', 'list', tile=None,
                       comments=comments, topic=topic,
                       variant=variant, root=root, recurse=recurse,
                       cached=cached, ret_url=ret_url)


def show(comment, recurse=True, ret_url=''):
    can_edit = can.comment.edit(comment)
    groups = sorted(c.user.groups if c.user else [])
    return render_tile('/comment/tiles.html', 'show', CommentTile(comment),
                       comment=comment, cached=True, can_edit=can_edit,
                       groups=groups, ret_url=ret_url, recurse=recurse)
