from util import render_tile, BaseTile

from pylons import tmpl_context as c

class DelegationTile(BaseTile):
    
    def __init__(self, delegation):
        self.delegation = delegation
    
    
    
def inbound(delegation):
    return render_tile('/delegation/tiles.html', 'inbound', 
                       DelegationTile(delegation), delegation=delegation,
                       user=c.user, cached=True)

def outbound(delegation):
    return render_tile('/delegation/tiles.html', 'outbound', 
                       DelegationTile(delegation), delegation=delegation,
                       user=c.user, cached=True)
    
def row(delegation):
    return render_tile('/delegation/tiles.html', 'row', 
                       DelegationTile(delegation), delegation=delegation)
    
def sidebar(delegateable):
    return render_tile('/delegation/tiles.html', 'sidebar', 
                       None, delegateable=delegateable, 
                       user=c.user, cached=True)
    