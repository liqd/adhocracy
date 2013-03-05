import logging

from pylons import config
from pylons import request
from pylons import tmpl_context as c
from pylons.decorators import validate
from pylons.i18n import _

import formencode
from formencode import validators, htmlfill

from adhocracy import forms
from adhocracy.lib.auth import guard, require
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render
from adhocracy.lib.templating import ret_success
from adhocracy.model import Instance
from adhocracy.model import Membership
from adhocracy.model import Message
from adhocracy.model import MessageRecipient
from adhocracy.model import Permission
from adhocracy.model import User

log = logging.getLogger(__name__)


class MassMessageForm(formencode.Schema):
    allow_extra_fields = True
    subject = validators.String(max=140, not_empty=True)
    body = validators.String(min=2, not_empty=True)
    instances = forms.MessageableInstances()


class MassmessageController(BaseController):
    """
    This deals with messages to multiple users at the same time. This will be
    will be merged with the MessageController at some point.
    """

    new_template = '/massmessage/new.html'

    @classmethod
    def get_allowed_instances(cls, user):
        # all instances in which the current user has permission to send a
        # message to
        needed_permission = Permission.find_multiple(
            ['instance.message', 'global.message'])

        return [m.instance for m in user.memberships
                if (m.instance is not None
                    and m.group.has_any_permission(needed_permission))]

    @classmethod
    def get_allowed_sender_options(cls, user):
        return {
            'noreply': (config.get('adhocracy.email.noreply'), True, True),
            'sender': (user.email, False, user.is_email_activated()),
        }

    def new(self, errors={}):
        require.perm('instance.message')

        defaults = dict(request.params)

        data = {
            'instances': self.get_allowed_instances(c.user),
            'sender_options': self.get_allowed_sender_options(c.user),
        }

        return htmlfill.render(render(self.new_template, data),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInternalRequest(methods=['POST'])
    @validate(schema=MassMessageForm(), form='new')
    def create(self):

        allowed_sender_options = self.get_allowed_sender_options(c.user)
        sender = self.form_result.get('sender')
        assert(sender in allowed_sender_options)
        sender_email, checked, enabled = allowed_sender_options[sender]
        assert(enabled)

        message = Message.create(self.form_result.get('subject'),
                                 self.form_result.get('body'),
                                 c.user,
                                 sender_email)

        # Determine recipients

        recipients = User.all_q().join(Membership).filter(
            Membership.instance_id.in_(self.form_result.get('instances')))

        for user in recipients:
            MessageRecipient.create(message, user, notify=True)

        return ret_success(message=_("Message sent to %d users." %
                                     recipients.count()))
