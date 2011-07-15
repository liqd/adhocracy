from pylons import tmpl_context as c

from adhocracy.model import Page, Proposal
from adhocracy.model.meta import Session
from adhocracy.lib import text
from adhocracy.lib.tiles.util import render_tile, BaseTile


class InstanceTile(BaseTile):

    def __init__(self, instance):
        self.instance = instance
        self.__issues = None
        self.__proposals_count = None
        self.__norms_count = None

    @property
    def description(self):
        if self.instance.description:
            return text.render(self.instance.description, escape=False)
        return ""

    @property
    def activation_delay(self):
        return self.instance.activation_delay

    @property
    def required_majority(self):
        return "%s%%" % int(self.instance.required_majority * 100)

    @property
    def num_proposals(self):
        if self.__proposals_count is None:
            query = Session.query(Proposal)
            query = query.filter(Proposal.instance == self.instance)
            query = query.filter(Proposal.delete_time == None)
            self.__proposals_count = query.count()
        return self.__proposals_count

    @property
    def num_norms(self):
        if self.__norms_count is None:
            query = Session.query(Page)
            query = query.filter(Page.instance == self.instance)
            query = query.filter(Page.delete_time == None)
            query = query.filter(Page.function == Page.NORM)
            self.__norms_count = query.count()
        return self.__norms_count


def row(instance):
    return render_tile('/instance/tiles.html', 'row', InstanceTile(instance),
                       instance=instance, user=c.user, cached=True)


def header(instance, tile=None, active='issues', no_panel=False):
    if tile is None:
        tile = InstanceTile(instance)
    return render_tile('/instance/tiles.html', 'header', tile,
                       instance=instance, active=active, no_panel=no_panel)
