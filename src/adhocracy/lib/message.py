from pylons.i18n import _

from adhocracy import config
from adhocracy.lib.templating import render
from adhocracy.model import meta


def email_subject(message, recipient, _format=None):
    if _format is None:
        _format = _(u"[{site_name}] Message from {sender_name}: {subject}")
    return _format.format(**{
        'subject': message.subject,
        'sender_name': message.creator.name,
        'site_name': config.get('adhocracy.site.name'),
    })


def email_body(message, recipient, template=None, massmessage=True):
    if template is None:
        template = "/message/body.txt"
    return render(template, data={
        'message': message,
        'recipient': recipient,
        'massmessage': massmessage,
    })


def _send(message, force_resend=False, massmessage=True,
          email_subject_format=None, email_body_template=None):
    from adhocracy.model import Notification
    from adhocracy.lib import mail, event

    if massmessage:
        event_type = event.T_MASSMESSAGE_SEND
    else:
        event_type = event.T_MESSAGE_SEND

    e = event.emit(event_type, message.creator,
                   message=message,
                   sender=message.creator)
    notification = Notification(e, message.creator)
    meta.Session.add(notification)

    for r in message.recipients:
        if force_resend or not r.email_sent:
            if (r.recipient.is_email_activated() and
                    r.recipient.email_messages):

                if message.creator.is_email_activated():
                    reply_to = message.creator.email
                else:
                    reply_to = None

                mail.to_user(r.recipient,
                             email_subject(message, r.recipient,
                                           email_subject_format),
                             email_body(message, r.recipient,
                                        email_body_template,
                                        massmessage=massmessage),
                             headers={},
                             decorate_body=False,
                             reply_to=reply_to,
                             name_from=message.creator.name)

            # creator already got a notification
            if r.recipient != message.creator:
                notification = Notification(e, r.recipient,
                                            type=event.N_MESSAGE_RECIEVE)
                meta.Session.add(notification)

            r.email_sent = True

    meta.Session.commit()
