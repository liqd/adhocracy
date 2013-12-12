from pylons.i18n import _
from pylons import config

from adhocracy.model import meta


def render_body(body, recipient, include_footer, is_preview=False):
    from adhocracy.lib import helpers as h
    from adhocracy.lib.templating import render
    from adhocracy.lib.auth.welcome import welcome_url

    if recipient.gender == 'f':
        salutation = _('Dear Ms.')
    elif recipient.gender == 'm':
        salutation = _('Dear Mr.')
    else:
        salutation = _('Dear')

    if is_preview:
        welcome_url = welcome_url(recipient,
                                  (u'X' * len(recipient.welcome_code)
                                   if recipient.welcome_code
                                   else u'NO_WELCOME_CODE_SET'))
    else:
        welcome_url = welcome_url(recipient, recipient.welcome_code)

    rendered_body = body.format(**{
        'uid': u'%d' % recipient.id,
        'name': recipient.name,
        'email': recipient.email,
        'welcome_url': welcome_url,
        'salutation': salutation,
    })

    return render("/massmessage/body.txt", {
        'body': rendered_body,
        'page_url': config.get('adhocracy.domain').strip(),
        'settings_url': h.entity_url(recipient,
                                     member='settings/notifications',
                                     absolute=True),
        'include_footer': include_footer,
    })


def _send(message, force_resend=False, massmessage=True):
    from adhocracy.model import Notification
    from adhocracy.lib import mail, event

    if massmessage:
        event_type = event.T_MASSMESSAGE_SEND
    else:
        event_type = event.T_MESSAGE_SEND

    e = event.emit(event_type, message.creator, instance=message.instance,
                   message=message,
                   sender=message.creator)
    notification = Notification(e, message.creator)
    meta.Session.add(notification)

    for r in message.recipients:
        if force_resend or not r.email_sent:
            if (r.recipient.is_email_activated() and
                    r.recipient.email_messages):

                body = render_body(message.body, r.recipient,
                                   message.include_footer)

                mail.to_user(r.recipient,
                             message.subject,
                             body,
                             headers={},
                             decorate_body=False,
                             email_from=message.email_from,
                             name_from=message.name_from)

            # creator already got a notification
            if r.recipient != message.creator:
                notification = Notification(e, r.recipient,
                                            type=event.N_MESSAGE_RECIEVE)
                meta.Session.add(notification)

            r.email_sent = True
>>>>>>> 3e1eb9b... enforce email_sent and force_resend
