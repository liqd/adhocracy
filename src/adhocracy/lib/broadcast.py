from datetime import datetime
import json

from pylons.i18n import _
from sqlalchemy import or_

import adhocracy.model as model
import adhocracy.i18n as i18n
from adhocracy.lib.queue import async
import mail


def notify_abuse(instance, user, url, message):
    message = {
        'instance': instance.key if instance else None,
        'user': user.user_name if user else 'Anonymous',
        'url': url,
        'message': message
    }
    message = json.dumps(message)
    handle_abuse_message(message)


def get_instance_admins(instance):
    sgroup = model.Group.find(model.Group.CODE_SUPERVISOR)
    agroup = model.Group.find(model.Group.CODE_ADMIN)
    q = model.meta.Session.query(model.User)
    q = q.join(model.Membership)
    q = q.filter(model.Membership.instance == instance)
    q = q.filter(or_(model.Membership.group == sgroup,
                     model.Membership.group == agroup))
    q = q.filter(or_(model.Membership.expire_time == None,
                     model.Membership.expire_time >= datetime.utcnow()))
    return q.all()


def get_global_admins():
    group = model.Group.find(model.Group.CODE_ADMIN)
    q = model.meta.Session.query(model.User)
    q = q.join(model.Membership)
    q = q.filter(model.Membership.instance == None)
    q = q.filter(model.Membership.group == group)
    q = q.filter(or_(model.Membership.expire_time == None,
                     model.Membership.expire_time >= datetime.utcnow()))
    return q.all()


@async
def handle_abuse_message(message):
    message = json.loads(message)
    admins = []
    if message.get('instance'):
        instance = model.Instance.find(message.get('instance'))
        admins = get_instance_admins(instance)
    else:
        admins = get_global_admins()
    for admin in admins:
        i18n.user_language(admin)
        subject = _("Abuse report: %s") % message.get('url')
        body = _("%(user)s has reported abuse on the page %(url)s:"
                 "\r\n\r\n%(message)s")
        body = body % message
        mail.to_user(admin, subject, body)
