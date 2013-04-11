import logging

import formencode
from formencode import htmlfill, validators, Invalid

from pylons import request
from pylons.controllers.util import abort, redirect
from pylons.i18n import _

from adhocracy import forms
from adhocracy.lib import helpers
from adhocracy.lib.auth import guard, csrf
from adhocracy.lib.base import BaseController
from adhocracy.lib.staticpage import (get_static_page, get_backend,
                                      all_languages, all_language_infos)
from adhocracy.lib.templating import render, ret_abort

log = logging.getLogger(__name__)

guard_perms = guard.perm("global.admin")


class EditForm(formencode.Schema):
    allow_extra_fields = True

    title = validators.String()
    body = validators.String()


class NewForm(EditForm):
    key = forms.StaticPageKey()
    lang = validators.OneOf(set(all_languages()))


class StaticController(BaseController):

    @guard_perms
    def index(self):
        data = {
            'static_pages': get_backend().all()
        }
        return render('/static/index.html', data)

    @guard_perms
    def new(self, errors=None):
        data = {
            'all_language_infos': list(all_language_infos())
        }
        defaults = dict(request.params)
        defaults['_tok'] = csrf.token_id()
        return htmlfill.render(render('/static/new.html', data),
                               defaults=defaults, errors=errors)

    @guard_perms
    @csrf.RequireInternalRequest(methods=['POST'])
    def make_new(self):
        try:
            form_result = NewForm().to_python(request.params)
        except Invalid as i:
            return self.new(errors=i.unpack_errors())

        key = form_result.get('key')
        lang = form_result.get('lang')

        backend = get_backend()
        if backend.get(key, lang) is not None:
            msg = _('Page does already exist. Select another key or language.')
            helpers.flash(msg, 'error')
            return self.new()

        backend.create(key,
                       lang,
                       form_result.get('title'),
                       form_result.get('body'))
        helpers.flash(_('Page updated'), 'notice')
        return redirect(helpers.base_url('/static/'))

    @guard_perms
    def edit(self, key, lang, errors=None):
        backend = get_backend()
        sp = backend.get(key, lang)
        if not sp:
            return ret_abort(_('Cannot find static page to edit'), code=404)
        data = {'staticpage': sp}
        defaults = {
            'title': sp.title,
            'body': sp.body,
        }
        defaults.update(dict(request.params))
        defaults['_tok'] = csrf.token_id()
        return htmlfill.render(render('/static/edit.html', data),
                               defaults=defaults, errors=errors)

    @guard_perms
    @csrf.RequireInternalRequest(methods=['POST'])
    def update(self, key, lang):
        backend = get_backend()
        sp = backend.get(key, lang)
        if not sp:
            return ret_abort(_('Cannot find static page to edit'), code=404)

        try:
            form_result = EditForm().to_python(request.params)
        except Invalid as i:
            return self.edit(errors=i.unpack_errors())

        sp.title = form_result.get('title')
        sp.body = form_result.get('body')
        sp.commit()
        helpers.flash(_('Page updated'), 'notice')
        return redirect(helpers.base_url('/static/'))

    def serve(self, key, format='html'):
        page = get_static_page(key)
        if page is None:
            return abort(404, _('The requested page was not found'))

        data = {
            'static': page,
            'active_global_nav': key,
        }
        if format == 'simple':
            ret = render('/plain_doc.html', data)
        else:
            ret = render('/template_doc.html', data)
        return ret
