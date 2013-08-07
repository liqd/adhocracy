from datetime import datetime
import logging

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from sqlalchemy import not_

from adhocracy import config
from adhocracy import model
from adhocracy.controllers.event import EventController
from adhocracy.lib import helpers as h
from adhocracy.lib import pager, sorting
from adhocracy.lib.auth import guard
from adhocracy.lib.base import BaseController
from adhocracy.lib.staticpage import add_static_content
from adhocracy.lib.templating import render
from adhocracy.lib.util import get_entity_or_abort

from proposal import ProposalFilterForm


log = logging.getLogger(__name__)


class RootController(BaseController):

    @guard.proposal.index()
    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format='html'):

        if c.instance:
            redirect(h.entity_url(c.instance))

        if format == 'rss':
            return EventController().all(format='rss')

        data = {}

        instances_in_root = config.get_int(
            'adhocracy.startpage.instances.list_length')
        if instances_in_root > 0:
            data['instances'] = model.Instance.all(limit=instances_in_root)
        elif instances_in_root == -1:
            data['instances'] = model.Instance.all()

        add_static_content(data, u'adhocracy.static_index_path')
        if data['title'] is None:
            data['title'] = config.get('adhocracy.site.name')

        proposals_number = config.get_int(
            'adhocracy.startpage.proposals.list_length')

        if proposals_number > 0:
            proposals = model.Proposal.all_q()\
                .join(model.Instance).filter(not_(
                    model.Instance.key.in_(model.Instance.SPECIAL_KEYS)))\
                .order_by(model.Proposal.create_time.desc())

            data['new_proposals_pager'] = pager.proposals(
                proposals, size=proposals_number,
                default_sort=sorting.entity_newest,
                enable_pages=False,
                enable_sorts=False)
        else:
            data['new_proposals_pager'] = None

        if config.get_bool('adhocracy.show_stats_on_frontpage'):
            data['stats_global'] = {
                "members": model.User.all_q().count(),
                "comments": model.Comment.all_q().count(),
                "proposals": model.Proposal.all_q().count(),
                "votes": model.Vote.all_q().count(),
            }

        return render('index.html', data)

    #@RequireInstance
    def dispatch_delegateable(self, id):
        dgb = get_entity_or_abort(model.Delegateable, id,
                                  instance_filter=False)
        redirect(h.entity_url(dgb))

    @guard.proposal.index()
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
                h.tutorial.disable(None, c.user)
            else:
                h.tutorial.disable(name, c.user)
        else:
            h.tutorial.enable()
