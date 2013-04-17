from datetime import datetime
from sqlalchemy import (
    Column,
    ForeignKey,
    MetaData,
    Table
)
from sqlalchemy import (
    Integer,
    DateTime,
    Unicode
)

metadata = MetaData()

#table to update
mediafile_table = Table(
    'mediafile', metadata,
    Column('id', Integer, primary_key=True),
    # mediacenter rest api identifier
    Column('name', Unicode(255), default=u'', nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id',
                                              ondelete="CASCADE",),
           nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
)

delegateable_mediafiles_table = Table(
    'delegateable_mediafiles', metadata,
    Column('id', Integer, primary_key=True),
    Column('mediafile_id', Integer, ForeignKey('mediafile.id'),
           nullable=False),
    Column('delegateable_id', Integer, ForeignKey('delegateable.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False)
)


comment_mediafiles_table = Table(
    'comment_mediafiles', metadata,
    Column('id', Integer, primary_key=True),
    Column('mediafile_id', Integer, ForeignKey('mediafile.id'),
           nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False)
)


def upgrade(migrate_engine):
    #use sqlalchemy-migrate database connection
    metadata.bind = migrate_engine
    #autoload needed tables
    instance_table = Table('instance', metadata, autoload=True)
    delegateable_table = Table('delegateable', metadata, autoload=True)
    comment_table = Table('comment', metadata, autoload=True)

    #create/recreate the table
    mediafile_table.create()
    delegateable_mediafiles_table.create()
    comment_mediafiles_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
