from datetime import datetime
import logging

from paste.deploy.converters import asint
from pylons import request, response, tmpl_context as c, config
from pylons.controllers.util import redirect
from pylons.decorators import validate

from adhocracy import model
from adhocracy.controllers.event import EventController
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import require
from adhocracy.lib.base import BaseController
from adhocracy.lib.static import StaticPage
from adhocracy.lib.templating import render
from adhocracy.lib.util import get_entity_or_abort

from proposal import ProposalFilterForm


log = logging.getLogger(__name__)


class RootController(BaseController):

    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format='html'):
        require.proposal.index()
        if c.instance:
            redirect(h.entity_url(c.instance))

        instances_in_root = asint(config.get('adhocracy.startpage.instances.list_length', 5))
        if instances_in_root > 0:
            c.instances = model.Instance.all(limit=instances_in_root)
        elif instances_in_root == -1:
            c.instances = model.Instance.all()

        c.page = StaticPage('index')

        #query = self.form_result.get('proposals_q')
        #proposals = libsearch.query.run(query,
        #                                entity_type=model.Proposal)[:10]
        c.milestones = model.Milestone.all()
        #c.proposals_pager = pager.proposals(proposals)
        #c.proposals = c.proposals_pager.here()
        c.stats_global = {
                "members": model.User.all_q().count(),
                "comments": model.Comment.all_q().count(),
                "proposals": model.Proposal.all_q().count(),
                "votes": model.Vote.all_q().count(),
            }

        if format == 'rss':
            return EventController().all(format='rss')

        return render('index.html')

    #@RequireInstance
    def dispatch_delegateable(self, id):
        dgb = get_entity_or_abort(model.Delegateable, id,
                                  instance_filter=False)
        redirect(h.entity_url(dgb))

    def sitemap_xml(self):
        if c.instance:
            redirect(h.base_url(None, path="/sitemap.xml"))
        c.delegateables = model.Delegateable.all()
        c.change_time = datetime.utcnow()
        response.content_type = "text/xml"
        return render("sitemap.xml")

    def robots_txt(self):
        response.content_type = "text/plain"
        if not c.instance:
            return render("robots.txt")
        return render("instance/robots.txt")

    def tutorials(self):
        if 'disable' in request.params:
            name = request.params.get('disable')
            if name == 'ALL':
                h.tutorial.disable(None)
            else:
                h.tutorial.disable(name)
        else:
            h.tutorial.enable()
