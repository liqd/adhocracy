from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate
import adhocracy.model as model

from .. import helpers as h
from .. import text

class MilestoneTile(BaseTile):

    def __init__(self, milestone):
        self.milestone = milestone

    @property
    def text(self):
        if self.milestone.text:
            return text.render(self.milestone.text, escape=False)
        return ""

def row(milestone):
    return render_tile('/milestone/tiles.html', 'row',
                       MilestoneTile(milestone),
                       milestone=milestone, cached=True)

def header(milestone, tile=None):
    if tile is None:
        tile = MilestoneTile(milestone)
    return render_tile('/milestone/tiles.html', 'header',
                       tile, milestone=milestone)


