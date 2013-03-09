import logging

from sqlalchemy import Table, Column, Integer, Unicode

import meta

log = logging.getLogger(__name__)

group_table = Table(
    'group', meta.data,
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False, unique=True),
    Column('code', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
)


class Group(object):

    CODE_ANONYMOUS = u"anonymous"
    CODE_ORGANIZATION = u"organization"
    CODE_OBSERVER = u"observer"
    CODE_ADVISOR = u"advisor"
    CODE_VOTER = u"voter"
    CODE_SUPERVISOR = u"supervisor"
    CODE_MODERATOR = u"moderator"
    CODE_ADMIN = u"admin"
    CODE_DEFAULT = u"default"
    CODE_ADDRESSEE = u"addressee"

    INSTANCE_GROUPS = [CODE_OBSERVER, CODE_VOTER, CODE_SUPERVISOR,
                       CODE_ADVISOR, CODE_MODERATOR, CODE_ADDRESSEE]
    INSTANCE_DEFAULT = CODE_VOTER

    def __init__(self, group_name, code, description=None):
        self.group_name = group_name
        self.code = code
        self.description = description

    @classmethod
    def all(cls):
        return meta.Session.query(Group).all()

    @classmethod
    def all_instance(cls):
        # todo: one query.
        return [cls.by_code(g) for g in cls.INSTANCE_GROUPS]

    @classmethod
    #@meta.session_cached
    def find(cls, group_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Group)
            q = q.filter(Group.group_name == group_name)
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    _index_id_attr = 'group_name'

    @classmethod
    #@meta.session_cached
    def by_id(cls, id):
        q = meta.Session.query(Group)
        q = q.filter(Group.id == id)
        return q.limit(1).first()

    @classmethod
    def by_code(cls, code):
        q = meta.Session.query(Group)
        q = q.filter(Group.code == code)
        return q.limit(1).first()

    def is_instance_group(self):
        return self.code in self.INSTANCE_GROUPS

    def __repr__(self):
        return u"<Group(%d,%s)>" % (self.id, self.code)

    def has_any_permission(self, permissions):
        return bool(set(permissions).intersection(set(self.permissions)))
