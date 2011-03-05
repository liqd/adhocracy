import logging

from formencode import validators, foreach, Schema

from pylons import tmpl_context as c, response
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, model
from adhocracy.lib import democracy
from adhocracy.lib import event, helpers as h, pager, sorting, tiles
from adhocracy.lib.auth import csrf, require
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import (render, render_json, ret_abort,
                                      ret_success)
from adhocracy.lib.util import get_entity_or_abort


log = logging.getLogger(__name__)


class DelegationNewForm(Schema):
    allow_extra_fields = True
    scope = forms.ValidDelegateable()


class DelegationCreateForm(DelegationNewForm):
    agent = foreach.ForEach(forms.ExistingUserName())
    replay = validators.Int(if_empty=1, if_missing=1, not_empty=False)


class DelegationController(BaseController):

    @RequireInstance
    def index(self, format='html'):
        require.delegation.index()
        c.delegations = model.Delegation.all(instance=c.instance)
        if format == 'dot':
            c.users = model.User.all(instance=c.instance)
            response.content_type = "text/plain"
            return render("/delegation/graph.dot")
        if format == 'json':
            c.delegations_pager = pager.delegations(c.delegations)
            return render_json(c.delegations_pager)
        return self.not_implemented(format=format)

    @RequireInstance
    @validate(schema=DelegationNewForm(), form="bad_request",
              post_only=False, on_get=True)
    def new(self):
        require.delegation.create()
        c.scope = self.form_result.get('scope')
        return render("/delegation/new.html")

    @RequireInstance
    @csrf.RequireInternalRequest(methods=["POST"])
    @validate(schema=DelegationCreateForm(), form="new", post_only=True)
    def create(self, format='html'):
        require.delegation.create()
        c.scope = self.form_result.get('scope')
        agents = filter(lambda f: f is not None, self.form_result.get('agent'))
        if not len(agents) or agents[0] == c.user:
            h.flash(_("Invalid delegation recipient"), 'error')
            return self.new()

        existing = model.Delegation.find_by_agent_principal_scope(agents[0],
                                                                  c.user,
                                                                  c.scope)
        if existing is not None:
            h.flash(_("You have already delegated voting to %s in %s") %
                    (agents[0].name, c.scope.label),
                    'notice')
            return self.new()

        delegation = model.Delegation.create(
            c.user, agents[0], c.scope,
            replay=self.form_result.get('replay') == 1)
        model.meta.Session.commit()

        event.emit(event.T_DELEGATION_CREATE, c.user,
                   instance=c.instance,
                   topics=[c.scope], scope=c.scope,
                   agent=agents[0], delegation=delegation)

        return ret_success(entity=delegation.scope, format=format)

    @RequireInstance
    @csrf.RequireInternalRequest()
    def delete(self, id):
        c.delegation = get_entity_or_abort(model.Delegation, id)
        require.delegation.delete(c.delegation)
        if not c.delegation.principal == c.user:
            return ret_abort(_("Cannot access delegation %(id)s") %
                             {'id': id}, code=403)
        c.delegation.revoke()
        model.meta.Session.commit()
        event.emit(event.T_DELEGATION_REVOKE, c.user,
                   topics=[c.delegation.scope],
                   scope=c.delegation.scope, instance=c.instance,
                   agent=c.delegation.agent)
        return ret_success(message=_("The delegation is now revoked."),
                           entity=c.delegation.scope)

    @RequireInstance
    def show(self, id, format='html'):
        c.delegation = get_entity_or_abort(model.Delegation, id)
        require.delegation.show(c.delegation)
        c.scope = c.delegation.scope
        decisions = democracy.Decision.for_user(c.delegation.principal,
                                                c.instance)
        decisions = filter(lambda d: c.delegation in d.delegations, decisions)
        decisions = filter(lambda d: isinstance(d.poll.subject,
                                                model.Proposal),
                           decisions)
        c.decisions_pager = pager.NamedPager(
            'decisions', decisions, tiles.decision.user_row,
            sorts={_("oldest"): sorting.entity_oldest,
                   _("newest"): sorting.entity_newest},
            default_sort=sorting.entity_newest)

        if format == 'json':
            return render_json((c.delegation, c.decisions_pager))

        return render("delegation/show.html")

    @RequireInstance
    def edit(self, format='html'):
        return self.not_implemented(format=format)

    @RequireInstance
    def update(self, format='html'):
        return self.not_implemented(format=format)
