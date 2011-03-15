import logging
import os.path

from babel import Locale

import formencode
from formencode import htmlfill
from formencode import validators

from pylons import request, response, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators import validate
from pylons.i18n import _

from adhocracy import forms, i18n, model
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib import event, helpers as h, logo, pager, sorting, text
from adhocracy.lib import tiles
from adhocracy.lib.auth import csrf, require
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import (render, render_json, render_png,
                                      ret_abort, ret_success)
from adhocracy.lib.util import get_entity_or_abort


log = logging.getLogger(__name__)


class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(validators.String(min=4, max=20),
                              forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)


class InstanceEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)
    default_group = forms.ValidGroup(not_empty=True)
    locale = validators.String(not_empty=False)
    allow_adopt = validators.StringBool(not_empty=False, if_empty=False,
                                        if_missing=False)
    allow_delegate = validators.StringBool(not_empty=False, if_empty=False,
                                           if_missing=False)
    allow_propose = validators.StringBool(not_empty=False, if_empty=False,
                                          if_missing=False)
    allow_index = validators.StringBool(not_empty=False, if_empty=False,
                                       if_missing=False)
    use_norms = validators.StringBool(not_empty=False, if_empty=False,
                                      if_missing=False)
    hidden = validators.StringBool(not_empty=False, if_empty=False,
                                   if_missing=False)


class InstanceController(BaseController):

    def index(self, format='html'):
        require.instance.index()
        h.add_meta("description",
                   _("An index of instances run at this site. "
                     "Select which ones you would like to join "
                     "and participate!"))
        instances = model.Instance.all()

        if format == 'json':
            return render_json(instances)

        c.instances_pager = pager.instances(instances)
        return render("/instance/index.html")

    def new(self):
        require.instance.create()
        return render("/instance/new.html")

    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceCreateForm(), form="new", post_only=True)
    def create(self, format='html'):
        require.instance.create()
        instance = model.Instance.create(
            self.form_result.get('key'), self.form_result.get('label'),
            c.user, description=self.form_result.get('description'),
            locale=c.locale)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_CREATE, c.user, instance=instance)
        return ret_success(entity=instance, format=format)

    #@RequireInstance
    def show(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.page_instance)

        if format == 'json':
            return render_json(c.page_instance)

        if format == 'rss':
            return self.activity(id, format)

        if c.page_instance != c.instance:
            redirect(h.entity_url(c.page_instance))

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        proposals = model.Proposal.all(instance=c.page_instance)
        c.new_proposals_pager = pager.proposals(
            proposals, size=7, enable_sorts=False,
            enable_pages=False, default_sort=sorting.entity_newest)
        pages = model.Page.all(instance=c.page_instance,
                functions=[model.Page.NORM])
        c.top_pages_pager = pager.pages(
            pages, size=7, enable_sorts=False,
            enable_pages=False, default_sort=sorting.norm_selections)
        tags = model.Tag.popular_tags(limit=40)
        c.tags = sorted(text.tag_cloud_normalize(tags),
                        key=lambda (k, c, v): k.name)

        c.stats = {
            'comments': model.Comment.all_q().count(),
            'proposals': model.Proposal.all_q(
                instance=c.page_instance).count(),
            'members': model.Membership.all_q().count()
        }
        return render("/instance/show.html")

    @RequireInstance
    def activity(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        require.instance.show(c.page_instance)

        if format == 'sline':
            sline = event.sparkline_samples(event.instance_activity,
                                            c.page_instance)
            return render_json(dict(activity=sline))

        events = model.Event.find_by_instance(c.page_instance)

        if format == 'rss':
            return event.rss_feed(events,
                                  _('%s News' % c.page_instance.label),
                                  h.base_url(c.page_instance),
                                  _("News from %s") % c.page_instance.label)

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        c.events_pager = pager.events(events)
        return render("/instance/activity.html")

    @RequireInstance
    def edit(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)

        c._Group = model.Group
        c.locales = i18n.LOCALES
        default_group = c.page_instance.default_group.code if \
                        c.page_instance.default_group else \
                        model.Group.INSTANCE_DEFAULT
        return htmlfill.render(
            render("/instance/edit.html"),
            defaults={
                '_method': 'PUT',
                'label': c.page_instance.label,
                'description': c.page_instance.description,
                'css': c.page_instance.css,
                'required_majority': c.page_instance.required_majority,
                'activation_delay': c.page_instance.activation_delay,
                'allow_adopt': c.page_instance.allow_adopt,
                'allow_delegate': c.page_instance.allow_delegate,
                'allow_propose': c.page_instance.allow_propose,
                'allow_index': c.page_instance.allow_index,
                'hidden': c.page_instance.hidden,
                'locale': c.page_instance.locale,
                'use_norms': c.page_instance.use_norms,
                '_tok': csrf.token_id(),
                'default_group': default_group})

    @RequireInstance
    @csrf.RequireInternalRequest(methods=['POST'])
    @validate(schema=InstanceEditForm(), form="edit", post_only=True)
    def update(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.edit(c.page_instance)
        c.page_instance.description = self.form_result.get('description')
        c.page_instance.label = self.form_result.get('label')
        c.page_instance.required_majority = self.form_result.get(
            'required_majority')
        c.page_instance.activation_delay = self.form_result.get(
            'activation_delay')
        c.page_instance.allow_adopt = self.form_result.get('allow_adopt')
        c.page_instance.allow_delegate = self.form_result.get('allow_delegate')
        c.page_instance.allow_propose = self.form_result.get('allow_propose')
        c.page_instance.allow_index = self.form_result.get('allow_index')
        c.page_instance.hidden = self.form_result.get('hidden')
        c.page_instance.css = self.form_result.get('css')
        c.page_instance.use_norms = self.form_result.get('use_norms')

        locale = Locale(self.form_result.get("locale"))
        if locale and locale in i18n.LOCALES:
            c.page_instance.locale = locale

        if (self.form_result.get('default_group').code in
            model.Group.INSTANCE_GROUPS):
            c.page_instance.default_group = self.form_result.get(
                'default_group')

        try:
            if ('logo' in request.POST and
                hasattr(request.POST.get('logo'), 'file') and
                request.POST.get('logo').file):
                logo.store(c.page_instance, request.POST.get('logo').file)
        except Exception, e:
            h.flash(unicode(e), 'error')
            log.debug(e)
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_EDIT, c.user, instance=c.page_instance)
        return ret_success(entity=c.page_instance, format=format)

    def icon(self, id, y=24, x=None):
        c.page_instance = model.Instance.find(id)
        try:
            y = int(y)
        except ValueError, ve:
            log.debug(ve)
            y = 24
        try:
            x = int(x)
        except:
            x = None
        (path, io) = logo.load(c.page_instance, size=(x, y))
        return render_png(io, os.path.getmtime(path))

    @RequireInstance
    def style(self, id):
        c.page_instance = self._get_current_instance(id)
        response.content_type = 'text/css'
        if c.page_instance.css:
            return c.page_instance.css
        return ''

    @RequireInstance
    def ask_delete(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.delete(c.page_instance)
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        return render('/instance/ask_delete.html')

    @csrf.RequireInternalRequest()
    def delete(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.delete(c.page_instance)
        c.page_instance.delete()
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_DELETE, c.user, instance=c.instance,
                   topics=[])
        return ret_success(format=format,
                           message=_("The instance %s has been deleted.") %
                           c.page_instance.label)

    @RequireInstance
    @csrf.RequireInternalRequest()
    def join(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        require.instance.join(c.page_instance)

        membership = model.Membership(c.user, c.page_instance,
                                      c.page_instance.default_group)
        model.meta.Session.expunge(membership)
        model.meta.Session.add(membership)
        model.meta.Session.commit()

        event.emit(event.T_INSTANCE_JOIN, c.user,
                   instance=c.page_instance)

        return ret_success(entity=c.page_instance, format=format,
                           message=_("Welcome to %(instance)s") % {
                            'instance': c.page_instance.label})

    def ask_leave(self, id):
        c.page_instance = self._get_current_instance(id)
        require.instance.leave(c.page_instance)

        c.tile = tiles.instance.InstanceTile(c.page_instance)
        return render('/instance/ask_leave.html')

    @csrf.RequireInternalRequest(methods=['POST'])
    def leave(self, id, format='html'):
        c.page_instance = self._get_current_instance(id)
        if not c.page_instance in c.user.instances:
            return ret_abort(
                entity=c.page_instance, format=format,
                message=_("You're not a member of %(instance)s.") % {
                                    'instance': c.page_instance.label})
        elif c.user == c.page_instance.creator:
            return ret_abort(
                entity=c.page_instance, format=format,
                message=_("You're the founder of %s, cannot leave.") % {
                                    'instance': c.page_instance.label})
        require.instance.leave(c.page_instance)

        for membership in c.user.memberships:
            if membership.is_expired():
                continue
            if membership.instance == c.page_instance:
                membership.expire()
                model.meta.Session.add(membership)

                c.user.revoke_delegations(c.page_instance)

                event.emit(event.T_INSTANCE_LEAVE, c.user,
                           instance=c.page_instance)
        model.meta.Session.commit()
        return ret_success(entity=c.page_instance, format=format,
                           message=_("You've left %(instance)s.") % {
                                'instance': c.page_instance.label})

    def _get_current_instance(self, id):
        if id != c.instance.key:
            abort(403, _("You cannot manipulate one instance from within "
                         "another instance."))
        return c.instance
