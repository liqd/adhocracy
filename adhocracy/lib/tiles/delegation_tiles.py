from util import render_tile, BaseTile

from pylons import tmpl_context as c

class DelegationTile(BaseTile):
    
    def __init__(self, delegation):
        self.delegation = delegation
    
    
    
def inbound(delegation):
    return render_tile('/delegation/tiles.html', 'inbound', 
                       DelegationTile(delegation), delegation=delegation)

def outbound(delegation):
    return render_tile('/delegation/tiles.html', 'outbound', 
                       DelegationTile(delegation), delegation=delegation)