from pylons.i18n import _

from adhocracy import config
from adhocracy.lib.templating import render
from adhocracy.model import meta
from adhocracy.model import Message, MessageRecipient


def render_body(body, recipient, is_preview=False):
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

    return body.format(**{
        'uid': u'%d' % recipient.id,
        'name': recipient.name,
        'email': recipient.email,
        'welcome_url': welcome_url,
        'salutation': salutation,
    })


def email_subject(message, recipient, _format=None):
    if _format is None:
        _format = _(u"[{site_name}] Message from {sender_name}: {subject}")
    return _format.format(**{
        'subject': message.subject,
        'sender_name': message.creator.name,
        'site_name': config.get('adhocracy.site.name'),
    })


def email_body(message, recipient, body, template=None, massmessage=True):
    if template is None:
        template = "/message/body.txt"
    return render(template, data={
        'message': message,
        'recipient': recipient,
        'massmessage': massmessage,
        'body': body,
    })


def _send(message, force_resend=False, massmessage=True,
          email_subject_format=None, email_body_template=None):
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

                body = render_body(message.body, r.recipient)

                mail.to_user(r.recipient,
                             email_subject(message, r.recipient,
                                           email_subject_format),
                             email_body(message, r.recipient, body,
                                        email_body_template,
                                        massmessage=massmessage),
                             headers={},
                             decorate_body=False,
                             email_from=message.email_from,
                             name_from=message.name_from)

            # creator already got a notification
            if r.recipient != message.creator:
                notification = Notification(e, r.recipient,
                                            type=event.N_MESSAGE_RECEIVE)
                meta.Session.add(notification)

            r.email_sent = True

    meta.Session.commit()


def send(subject, body, creator, recipients, sender_email=None,
         sender_name=None, instance=None, include_footer=True,
         massmessage=True, email_subject_format=None,
         email_body_template=None):

    message = Message.create(subject, body, creator,
                             sender_email=sender_email,
                             sender_name=sender_name,
                             instance=instance,
                             include_footer=include_footer)

    for recipient in recipients:
        MessageRecipient.create(message, recipient)

    _send(message,
          massmessage=massmessage,
          email_subject_format=email_subject_format,
          email_body_template=email_body_template)

    return message
