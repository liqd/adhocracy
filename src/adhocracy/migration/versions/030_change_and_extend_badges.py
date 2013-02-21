from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode

metadata = MetaData()

badge_table = Table(
    'badge', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('group', Integer, ForeignKey('group.id', ondelete="CASCADE")))


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    group_table = Table('group', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)

    # nullable=False does not work with sqlite even with default=...
    # and .create(populate_default=True). Alter with nullable=True
    # and change afterwards.
    description = Column('description', Unicode(255), default=u'',
                         nullable=True)
    description.create(badge_table, populate_default=True)
    description.alter(nullable=False)

    group_id = Column('group_id', Integer,
                      ForeignKey('group.id', ondelete="CASCADE"))
    group_id.create(badge_table)

    display_group = Column('display_group', Boolean, default=False)
    display_group.create(badge_table)

    q = migrate_engine.execute(badge_table.select())
    for (id, _, _, _, group_id, _, _, _) in q:
        update_statement = badge_table.update(
            badge_table.c.id == id,
            {'group_id': group_id,
             'description': '',
             'display_group': True})
        migrate_engine.execute(update_statement)

    badge_table.c.group.drop()


def downgrade(migrate_engine):
    raise NotImplementedError()
