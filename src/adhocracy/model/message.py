import logging
from datetime import datetime

from pylons import config
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

from adhocracy.model import meta

log = logging.getLogger(__name__)


message_table = Table(
    'message', meta.data,
    Column('id', Integer, primary_key=True),
    Column('subject', Unicode(140), nullable=False),
    Column('body', UnicodeText(), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('sender_email', Unicode(255), nullable=False),
)


class Message(meta.Indexable):

    def __init__(self, subject, body, creator, sender_email):
        self.subject = subject
        self.body = body
        self.creator = creator
        self.sender_email = sender_email

    @classmethod
    def create(cls, subject, body, creator, sender_email):
        message = cls(subject, body, creator, sender_email)
        meta.Session.add(message)
        meta.Session.flush()
        return message

    def render_body(self, user):
        import adhocracy.lib.message
        return adhocracy.lib.message.render_body(self.body, user)


message_recipient_table = Table(
    'message_recipient', meta.data,
    Column('id', Integer, primary_key=True),
    Column('message_id', Integer, ForeignKey('message.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email_sent', Boolean, default=False),
)


class MessageRecipient(object):

    def __init__(self, message, recipient):
        self.message = message
        self.recipient = recipient

    @classmethod
    def create(cls, message, recipient, notify=False):
        recipient = cls(message, recipient)
        meta.Session.add(recipient)
        meta.Session.flush()
        if notify:
            recipient.notify()
        return recipient

    def notify(self, force_resend=False):

        if (self.recipient.is_email_activated() and
           self.recipient.email_messages):

            from adhocracy.lib import helpers as h
            from adhocracy.lib import mail
            from adhocracy.lib.templating import render

            body = render("/massmessage/body.txt", {
                'body': self.message.render_body(self.recipient),
                'page_url': config.get('adhocracy.domain').strip(),
                'settings_url': h.entity_url(self.recipient,
                                             member='edit',
                                             absolute=True),
            })

            mail.to_user(self.recipient,
                         self.message.subject,
                         body,
                         headers={},
                         decorate_body=False,
                         email_from=self.message.sender_email)
