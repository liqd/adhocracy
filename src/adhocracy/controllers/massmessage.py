import logging

from pylons import config
from pylons import request
from pylons import tmpl_context as c
from pylons.decorators import validate
from pylons.i18n import _
from paste.deploy.converters import asbool

import formencode
from formencode import validators, htmlfill

from adhocracy import forms
from adhocracy.controllers.instance import InstanceController
from adhocracy.lib.auth import require
from adhocracy.lib.auth.authorization import has
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


class MassmessageForm(formencode.Schema):
    allow_extra_fields = True
    subject = validators.String(max=140, not_empty=True)
    body = validators.String(min=2, not_empty=True)
    instances = forms.MessageableInstances()
    sender = validators.String(not_empty=True)


class MassmessageController(BaseController):
    """
    This deals with messages to multiple users at the same time. This will be
    will be merged with the MessageController at some point.
    """

    @classmethod
    def get_allowed_instances(cls, user):
        """
        returns all instances in which the given user has permission to send a
        message to all users
        """
        if has('global.message'):
            return Instance.all()
        else:
            return [m.instance for m in user.memberships
                    if (m.instance is not None
                        and m.instance.is_authenticated
                        and 'instance.message' in m.group.permissions)]

    @classmethod
    def get_allowed_sender_options(cls, user):
        sender_options = {
            'user': {
                'email': user.email,
                'checked': False,
                'enabled': user.is_email_activated(),
                'reason': _("Email isn't activated"),
            },
            'system': {
                'email': config.get('adhocracy.email.from'),
                'checked': False,
                'enabled': asbool(config.get(
                    'allow_system_email_in_mass_messages', 'true')),
                'reason': _("Not permitted in system settings"),
            }
        }

        if sender_options['user']['enabled']:
            sender_options['user']['checked'] = True
        elif sender_options['system']['enabled']:
            sender_options['system']['checked'] = True

        return sender_options

    def new(self, id=None, errors={}):

        if id is None:
            require.perm('global.message')
            template = '/massmessage/new.html'
        else:
            c.page_instance = InstanceController._get_current_instance(id)
            require.message.create(c.page_instance)
            c.settings_menu = InstanceController.settings_menu(c.page_instance,
                                                               'massmessage')
            template = '/instance/settings_massmessage.html'

        defaults = dict(request.params)

        data = {
            'instances': self.get_allowed_instances(c.user),
            'sender_options': self.get_allowed_sender_options(c.user),
        }

        return htmlfill.render(render(template, data),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @RequireInternalRequest(methods=['POST'])
    @validate(schema=MassmessageForm(), form='new')
    def create(self):

        allowed_sender_options = self.get_allowed_sender_options(c.user)
        sender = self.form_result.get('sender')
        assert(sender in allowed_sender_options)
        assert allowed_sender_options[sender]['enabled']

        message = Message.create(self.form_result.get('subject'),
                                 self.form_result.get('body'),
                                 c.user,
                                 allowed_sender_options[sender]['email'])

        # Determine recipients

        recipients = User.all_q().join(Membership).filter(
            Membership.instance_id.in_(self.form_result.get('instances')))

        for user in recipients:
            MessageRecipient.create(message, user, notify=True)

        return ret_success(message=_("Message sent to %d users." %
                                     recipients.count()))
