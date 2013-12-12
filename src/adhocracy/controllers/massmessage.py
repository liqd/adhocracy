import logging

from pylons import request
from pylons import tmpl_context as c
from pylons.decorators import validate
from pylons.i18n import _

import formencode
from formencode import validators, htmlfill

from adhocracy import forms
from adhocracy.controllers.instance import InstanceController
from adhocracy.lib.auth import require
from adhocracy.lib.auth.authorization import has
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib import helpers as h
from adhocracy.lib.message import send as send_message
from adhocracy.lib.base import BaseController
from adhocracy.lib.templating import render, ret_success
from adhocracy.model import Instance
from adhocracy.model import Membership
from adhocracy.model import Permission
from adhocracy.model import User
from adhocracy.model import UserBadge
from adhocracy.model import UserBadges

log = logging.getLogger(__name__)


class MassmessageForm(formencode.Schema):
    allow_extra_fields = True
    subject = validators.String(max=140, not_empty=True)
    body = validators.String(min=2, not_empty=True)
    filter_instances = forms.MessageableInstances(not_empty=True)
    filter_badges = forms.ValidUserBadges()


def _get_options(func):
    """ Decorator that calls the functions with the following parameters:
        subject      - Subject of the message
        body         - Body of the message
        recipients   - A list of users the email is going to
    """
    @RequireInternalRequest(methods=['POST'])
    @validate(schema=MassmessageForm(), form='new')
    def wrapper(self):
        recipients = User.all_q()
        filter_instances = self.form_result.get('filter_instances')
        recipients = recipients.join(Membership).filter(
            Membership.instance_id.in_(filter_instances))
        filter_badges = self.form_result.get('filter_badges')
        if filter_badges:
            recipients = recipients.join(UserBadges,
                                         UserBadges.user_id == User.id)
            recipients = recipients.filter(
                UserBadges.badge_id.in_([fb.id for fb in filter_badges]))

        if len(filter_instances) == 1:
            instance = Instance.find(filter_instances[0])
        else:
            instance = None

        return func(self,
                    self.form_result.get('subject'),
                    self.form_result.get('body'),
                    recipients.all(),
                    instance=instance,
                    )
    return wrapper


class MassmessageController(BaseController):
    """
    This deals with messages to multiple users at the same time. This will be
    will be merged with the MessageController at some point.
    """

    @classmethod
    def _get_allowed_instances(cls, user):
        """
        returns all instances in which the given user has permission to send a
        message to all users
        """
        if has('global.message'):
            return Instance.all()
        else:
            perm = Permission.find('instance.message')
            instances = [m.instance for m in user.memberships
                         if (m.instance is not None
                             and m.instance.is_authenticated
                             and perm in m.group.permissions)]
            return sorted(instances, key=lambda i: i.label)

    def new(self, id=None, errors={}, format=u'html'):

        if id is None:
            require.perm('global.message')
            template = '/massmessage/new.html'
        else:
            c.page_instance = InstanceController._get_current_instance(id)
            require.message.create(c.page_instance)
            template = '/instance/message.html'

        defaults = dict(request.params)

        data = {
            'instances': self._get_allowed_instances(c.user),
            'userbadges': UserBadge.all(instance=c.instance)
        }

        return htmlfill.render(render(template, data,
                                      overlay=format == u'overlay'),
                               defaults=defaults, errors=errors,
                               force_defaults=False)

    @_get_options
    def create(self, subject, body, recipients, instance=None):
        send_message(subject, body, c.user, recipients, instance=instance)
        return ret_success(
            message=_("Message sent to %d users.") % len(recipients))
