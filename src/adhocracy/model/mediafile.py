'''
MediaFiles stored in adhocarcy_kotti.mediacenter.
A MediaFile is mainly a name to reference a resource in the mediacenter
and some helper scripts to work with the medicenter rest api.
MediaFiles can be added to proposals.
'''

from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, DateTime, Unicode

from adhocracy.model import meta, instance_filter as ifilter

log = logging.getLogger(__name__)
MARKER = object()


mediafile_table = Table(
    'mediafile', meta.data,
    Column('id', Integer, primary_key=True),
    # mediacenter rest api identifier
    Column('name', Unicode(255), default=u'', nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id',
                                              ondelete="CASCADE",),
           nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
)


delegateable_mediafiles_table = Table(
    'delegateable_mediafiles', meta.data,
    Column('id', Integer, primary_key=True),
    Column('mediafile_id', Integer, ForeignKey('mediafile.id'),
           nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False)
)


comment_mediafiles_table = Table(
    'comment_mediafiles', meta.data,
    Column('id', Integer, primary_key=True),
    Column('mediafile_id', Integer, ForeignKey('mediafile.id'),
           nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False)
)


class MediaFile(object):

    def __init__(self, name, instance=None):
        self.name = name
        self.instance = instance

    @classmethod
    def create(cls, name, instance=None):
        mediafile = cls(name, instance)
        meta.Session.add(mediafile)
        meta.Session.flush()
        return mediafile

    def __repr__(self):
        return "<%s(%s,%s)>" % (self.__class__.__name__, self.id,
                                self.name.encode('ascii', 'replace'))

    def __unicode__(self):
        return self.name

    @classmethod
    def count(cls):
        return meta.Session.query(cls).count()

    def __le__(self, other):
        return self.name >= other.name

    def __lt__(self, other):
        return self.name > other.name

    @classmethod
    def by_id(cls, id, instance_filter=True):
        try:
            q = meta.Session.query(cls)
            q = q.filter(cls.id == id)
            if ifilter.has_instance() and instance_filter:
                q = q.filter((cls.instance_id ==
                              ifilter.get_instance().id))
            return q.limit(1).first()
        except Exception, e:
            log.warn("by_id(%s): %s" % (id, e))
            return None

    @classmethod
    def find(cls, name_or_id):
        q = meta.Session.query(cls)
        try:
            q = q.filter(cls.id == int(name_or_id))
        except ValueError:
            q = q.filter(cls.name.like(name_or_id))
        return q.first()

    @classmethod
    def findall_by_ids(cls, ids):
        if len(ids) == 0:
            return []
        q = meta.Session.query(cls)
        q = q.filter(cls.id.in_(ids))
        return q.all()

    @classmethod
    def all_q(cls, instance=MARKER):
        '''
        A preconfigured query for all MediaFiles ordered by name.
        If *instance* is not given all mediafiles are given.
        If *instance* is given (either `None` or an instance object),
        only these mediafiles are returned.
        '''
        q = meta.Session.query(cls)
        if instance is not MARKER:
            q = q.filter(cls.instance == instance)
        return q

    @classmethod
    def all(cls, instance=None, include_global=False):
        """
        Return all mediafiles, orderd by name.
        Without instance it only returns mediafiles not bound to an instance.
        With instance it only returns mediafiles bound to that instance.
        With instance and include_global it returns both mediafiles bound to
        that instance and mediafiles not bound to an instance.
        """
        q = cls.all_q(instance=instance)
        if include_global and instance is not None:
            q = q.union(cls.all_q(instance=None))
        return q.order_by(cls.name).all()

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    instance=self.instance.id if self.instance else None)

    def assignDelegateable(self, delegateable, creator):
        DelegateableMediaFiles.create(delegateable, self, creator)
        meta.Session.refresh(delegateable)
        meta.Session.refresh(self)

    def assignComment(self, comment, creator):
        CommentMediaFiles.create(comment, self, creator)
        meta.Session.refresh(comment)
        meta.Session.refresh(self)


class BaseMediaFiles(object):
    '''class for entity<->MediaFile relations'''

    assigned_entity_name = "dummyentity"

    def __init__(self, entity, mediafile, creator):
        setattr(self, self.assigned_entity_name, entity)
        self.mediafile = mediafile
        self.creator = creator

    def __repr__(self):
        title = self.mediafile.name.encode('ascii', 'replace')
        return "<%smediafiles(%s, mediafile %s/%s for %s %s)>"\
               % (self.assigned_entity_name, self.id, self.mediafile.id, title,
                  self.assigned_entity_name,
                  getattr(self, self.assigned_entity_name).id)

    @classmethod
    def create(cls, entity, mediafile, creator):
        entitymediafile = cls(entity, mediafile, creator)
        meta.Session.add(entitymediafile)
        meta.Session.flush()
        return entitymediafile

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    @classmethod
    def find(cls, id):
        q = meta.Session.query(cls)
        q = q.filter(cls.id == id)
        return q.limit(1).first()


class DelegateableMediaFiles(BaseMediaFiles):
    '''class for Delegateable<->MediaFile relations'''

    assigned_entity_name = "delegateable"


class CommentMediaFiles(BaseMediaFiles):
    '''class for Comment<->MediaFile relations'''

    assigned_entity_name = "comment"
