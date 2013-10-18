from sqlalchemy import MetaData, Column, Table, ForeignKey, Integer, Unicode


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    event_table = Table('event', meta, autoload=True)
    user_table = Table('user', meta, autoload=True)
    watch_table = Table('watch', meta, autoload=True)

    notification_table = Table(
        'notification', meta,
        Column('id', Integer, primary_key=True),
        Column('event_id', Integer, ForeignKey('event.id'), nullable=False),
        Column('event_type', Unicode(255), nullable=True),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('watch_id', Integer, ForeignKey('watch.id'), nullable=True)
    )

    notification_table.create()
