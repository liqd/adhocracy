from pylons import tmpl_context as c

from adhocracy.lib.tiles.util import render_tile, BaseTile


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


def sidebar(delegateable, tile):
    return render_tile('/delegation/tiles.html', 'sidebar',
                       tile=tile, delegateable=delegateable,
                       user=c.user, cached=True)
