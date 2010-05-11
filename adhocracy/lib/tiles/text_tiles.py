from util import render_tile, BaseTile

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _ 

from webhelpers.text import truncate

import adhocracy.model as model
from .. import helpers as h
from .. import text
from .. import sorting

class TextTile(BaseTile):
    
    def __init__(self, text):
        self.text = text 
    

    @property
    def page(self):
        return self.text.page
    
    
    @property
    def parent_text_diff(self):
        if not self.text.parent:
            return self.text.render()
        return text.html_diff(self.text.parent.render(), 
                              self.text.render())
        
    @property 
    def parent_title_diff(self):
        if not self.text.parent:
            return self.text.title
        return text.html_diff(self.text.parent.title,
                              self.text.title)
    
    
    @property
    def comment_count(self):
        return len([c for c in self.comments()])
    
                                    
    def comments(self):
        from comment_tiles import CommentTile
        comments = sorting.comment_order(self.page.variant_comments(self.text.variant))
        for comment in comments:
            if comment.reply: 
                continue
            tile = CommentTile(comment)
            yield (comment, tile)


     
def history_row(text):
    return render_tile('/text/tiles.html', 'history_row', 
                       TextTile(text), text=text)
    
def full(text):
    return render_tile('/text/tiles.html', 'full', 
                       TextTile(text), text=text)

def comments(text):
    return render_tile('/text/tiles.html', 'comments', 
                       TextTile(text), text=text)
                       
def descbox(this, other, options=None, field=None):
    return render_tile('/text/tiles.html', 'descbox', TextTile(this),
                       this=this, other=other, options=options, field=field)
                       