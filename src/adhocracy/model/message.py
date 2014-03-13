import logging
from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

import meta
import instance_filter as ifilter

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
    Column('sender_email', Unicode(255), nullable=True),
    Column('include_footer', Boolean, default=True, nullable=False),
    Column('sender_name', Unicode(255), nullable=True),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True)
)


class Message(meta.Indexable):

    def __init__(self, subject, body, creator, sender_email=None,
                 sender_name=None, instance=None, include_footer=True):
        self.subject = subject
        self.body = body
        self.creator = creator
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.include_footer = include_footer
        self.instance = instance

    @classmethod
    def create(cls, subject, body, creator, sender_email=None,
               sender_name=None, instance=None, include_footer=True):
        message = cls(subject, body, creator, sender_email, sender_name,
                      instance, include_footer)
        meta.Session.add(message)
        meta.Session.flush()
        return message

    @classmethod
    def all_q(cls, instance=None, include_deleted=False):
        query = meta.Session.query(Message)
        if instance is not None:
            query = query.filter(Message.instance == instance)  # noqa
        if not include_deleted:
            query = query.filter(or_(Message.delete_time == None,  # noqa
                                     Message.delete_time > datetime.utcnow()))
        return query

    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        if instance_filter and ifilter.has_instance():
            instance = ifilter.get_instance()
        else:
            instance = None
        query = cls.all_q(instance=instance,
                          include_deleted=include_deleted)
        query = query.filter(Message.id == id)
        return query.first()

    @classmethod
    def all(cls, instance=None, include_deleted=False):
        return cls.all_q(instance=instance,
                         include_deleted=include_deleted).all()

    @property
    def email_from(self):
        if self.sender_email:
            return self.sender_email
        elif self.creator.is_email_activated():
            return self.creator.email
        else:
            return None

    @property
    def name_from(self):
        if self.sender_name:
            return self.sender_name
        else:
            return self.creator.name

    def rendered_body(self, user):
        from adhocracy.lib.message import render_body

        return render_body(self.body, user)


message_recipient_table = Table(
    'message_recipient', meta.data,
    Column('id', Integer, primary_key=True),
    Column('message_id', Integer, ForeignKey('message.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False),

    # recycled to mean 'sent' in any way, including notification
    Column('email_sent', Boolean, default=False),
)


class MessageRecipient(object):

    def __init__(self, message, recipient):
        self.message = message
        self.recipient = recipient

    @classmethod
    def create(cls, message, recipient):
        r = cls(message, recipient)
        meta.Session.add(r)
        meta.Session.flush()
        return r
