from sqlalchemy import Table, Column
from sqlalchemy import Integer, Unicode, ForeignKey
from adhocracy.model.badge import UserBadge
from adhocracy.model import meta

treatment_table = Table(
    'treatment', meta.data,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(40), nullable=False, unique=True),
    Column('variant_count', Integer, nullable=False),
)


class Treatment(object):
    def __init__(self, key, source_badges, variant_count):
        self.key = key
        self.source_badges = source_badges
        self.variant_count = variant_count

    @classmethod
    def create(cls, key, source_badges, variant_count):
        entry = cls(key, source_badges, variant_count)
        for i in range(variant_count):
            UserBadge.create(title=u'treatment-%s-%s' % (key, i),
                             color=u'', visible=False, description=u'')
        meta.Session.add(entry)
        meta.Session.flush()
        return entry

    @classmethod
    def find(cls, key):
        q = meta.Session.query(cls)
        q = q.filter(cls.key == key)
        return q.first()

    @classmethod
    def all(cls):
        q = meta.Session.query(cls)
        return sorted(q.all(), key=lambda t: t.key)

    @property
    def _variant_badges(self):
        return [self.get_variant_badge(i) for i in range(self.variant_count)]

    def get_assigned_users(self):
        """ Return a list(with one element for each variant) of the lists of
        assigned users. """
        return [vb.users for vb in self._variant_badges]

    def get_variant_badge(self, variant_id):
        return UserBadge.find('treatment-%s-%s' % (self.key, variant_id))

    def __repr__(self):
        return (u'<%s.%s(id=%r, key=%r, %r)>' %
                (self.__module__, type(self).__name__,
                 self.id, self.key, self.variant_count))


treatment_source_badges_table = Table(
    'treatment_source_badges', meta.data,
    Column('treatment_id', Integer,
           ForeignKey('treatment.id', ondelete='CASCADE')),
    Column('badge_id', Integer,
           ForeignKey('badge.id', ondelete='CASCADE')),
)
