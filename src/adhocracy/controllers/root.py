from datetime import datetime
import logging

from paste.deploy.converters import asbool, asint
from pylons import request, response, tmpl_context as c, config
from pylons.controllers.util import redirect
from pylons.decorators import validate
from sqlalchemy import not_

from adhocracy import model
from adhocracy.controllers.event import EventController
from adhocracy.lib import helpers as h
from adhocracy.lib import pager, sorting
from adhocracy.lib.auth import require
from adhocracy.lib.base import BaseController
from adhocracy.lib.static import get_static_page
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

        instances_in_root = asint(
            config.get('adhocracy.startpage.instances.list_length', 0))
        if instances_in_root > 0:
            c.instances = model.Instance.all(limit=instances_in_root)
        elif instances_in_root == -1:
            c.instances = model.Instance.all()

        c.page = get_static_page('index')

        proposals_number = asint(
            config.get('adhocracy.startpage.proposals.list_length', 0))

        if proposals_number > 0:
            proposals = model.Proposal.all_q()\
                .join(model.Instance).filter(not_(
                    model.Instance.key.in_(model.Instance.SPECIAL_KEYS)))\
                .order_by(model.Proposal.create_time.desc())

            c.new_proposals_pager = pager.proposals(
                proposals, size=proposals_number,
                default_sort=sorting.entity_newest,
                enable_pages=False,
                enable_sorts=False)
        else:
            c.new_proposals_pager = None

        if asbool(config.get('adhocracy.show_stats_on_frontpage', 'true')):
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
            redirect(h.base_url('/sitemap.xml', None))
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
