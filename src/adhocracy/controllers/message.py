import logging

from formencode import htmlfill, Invalid, Schema, validators

from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import helpers as h
from adhocracy.lib.auth import require
from adhocracy.lib.base import BaseController
from adhocracy.lib.instance import RequireInstance
from adhocracy.lib.templating import render
from adhocracy.lib.util import get_entity_or_abort

log = logging.getLogger(__name__)


class MessageCreateForm(Schema):
    allow_extra_fields = True
    subject = validators.String(max=250, not_empty=True)
    body = validators.String(max=20000, min=2, not_empty=True)


class MessageController(BaseController):

    @RequireInstance
    def new(self, id, format='html', errors={}):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.message(c.page_user)
        html = render("/message/new.html")
        return htmlfill.render(html, defaults=request.params,
                               errors=errors, force_defaults=False)

    @RequireInstance
    def create(self, id, format='html'):
        c.page_user = get_entity_or_abort(model.User, id)
        require.user.message(c.page_user)
        try:
            self.form_result = MessageCreateForm().to_python(request.params)
        except Invalid, i:
            return self.new(id, errors=i.unpack_errors())

        c.body = self.form_result.get('body')
        c.subject = self.form_result.get('subject')
        message = render("/message/body.txt")
        headers = {}
        if c.user.is_email_activated():
            headers['Reply-To'] = c.user.email

        from adhocracy.lib.mail import to_user
        subject = _("[%s] Message from %s: %s") % (c.instance.label,
                                                   c.user.name, c.subject)
        to_user(c.page_user, subject, message, headers=headers)

        h.flash(_("Your message has been sent. Thanks."), 'success')
        redirect(h.entity_url(c.page_user, instance=c.instance))
