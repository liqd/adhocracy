from .. import democracy
from .. import helpers as h
from ..auth import authorization as auth

from util import render_tile, BaseTile

class DecisionTile(BaseTile):
    
    def __init__(self, decision):
        self.decision = decision
        
def scope_row(decision):
    return render_tile('/decision/tiles.html', 'row', DecisionTile(decision), 
                       decision=decision, focus_user=True)
    
def user_row(decision):
    return render_tile('/decision/tiles.html', 'row', DecisionTile(decision), 
                       decision=decision, focus_scope=True)
    