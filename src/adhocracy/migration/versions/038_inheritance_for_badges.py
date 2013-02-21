'''
Migragte badges to use different models with shared table inheritance
instead of hand made queries.
'''
from datetime import datetime

from sqlalchemy import (MetaData, Boolean, Column, ForeignKey, DateTime,
                        Integer, String, Table, Unicode)

metadata = MetaData()


def are_elements_equal(x, y):
    return x == y


badge_table = Table(
    'badge', metadata,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    #badges for groups/users
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    #badges for delegateables
    Column('badge_delegateable', Boolean, default=False),
    #badges to make categories for delegateables
    Column('badge_delegateable_category', Boolean, default=False),
    #badges only valid inside an specific instance
    Column('instance_id', Integer, ForeignKey('instance.id',
                                        ondelete="CASCADE",), nullable=True))


USER_BADGE = 'user'
DELEGATEABLE_BADGE = 'delegateable'
CATEGORY_BADGE = 'category'


def upgrade(migrate_engine):

    metadata.bind = migrate_engine

    # dummy definitions to satisfy foreign keys
    Table('instance', metadata, autoload=True)
    Table('group', metadata, autoload=True)

    # add the column for the polymorphic identity
    # we have to use 'nullable=True' cause the values are
    # null when the column is created
    type_col = Column('type', String(40), nullable=True)
    type_col.create(badge_table)

    # fill column with the right values
    select = badge_table.select().with_only_columns(
        ['id', 'title', 'badge_delegateable', 'badge_delegateable_category'])
    badges_query_result = migrate_engine.execute(select)
    for values in badges_query_result:
        (id_, title, delegateable, category) = values
        if category:
            type_ = CATEGORY_BADGE
        elif delegateable:
            type_ = DELEGATEABLE_BADGE
        else:
            type_ = USER_BADGE
        update = badge_table.update().values(type=type_).where(
            badge_table.c.id == id_)
        migrate_engine.execute(update)

    # drop the old columns
    badge_table.c.badge_delegateable.drop()
    badge_table.c.badge_delegateable_category.drop()

    type_col.alter(nullable=False)


def downgrade(migrate_engine):
    raise NotImplementedError()
