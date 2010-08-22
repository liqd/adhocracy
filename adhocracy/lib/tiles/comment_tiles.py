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
    def show(self):
        if self.comment.is_deleted():
            children = map(lambda c: CommentTile(c).show, self.comment.replies) 
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
    def is_low(self):
        return self.score <= -1
    
    

def row(comment):
    return render_tile('/comment/tiles.html', 'row', CommentTile(comment), comment=comment)    


def header(comment, tile=None, active='comment'):
    if tile is None:
        tile = CommentTile(comment)
    return render_tile('/comment/tiles.html', 'header', tile, 
                       comment=comment, active=active)


def list(topic, root=None, comments=None, variant=None, recurse=True, ret_url=''):
    if comments is None:
        comments = topic.comments
    return render_tile('/comment/tiles.html', 'list', tile=None, comments=comments, topic=topic, 
                        variant=variant, root=root, recurse=recurse, cached=False, ret_url=ret_url)


def show(comment, recurse=True, ret_url=''):
    return render_tile('/comment/tiles.html', 'full', CommentTile(comment), 
                       comment=comment, comments=comment.topic.comments, recurse=recurse, ret_url=ret_url)
