from datetime import datetime
from sqlalchemy import MetaData, Column, Table, ForeignKey, func
from sqlalchemy import (Boolean, DateTime, Float, Integer, String, Unicode,
                        UnicodeText)

metadata = MetaData()

instance_table = Table(
    'instance', metadata,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(),
           onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'),
           nullable=True),
    Column('allow_adopt', Boolean, default=True),
    Column('allow_delegate', Boolean, default=True),
    Column('allow_propose', Boolean, default=True),
    Column('allow_index', Boolean, default=True),
    Column('hidden', Boolean, default=False),
    Column('locale', Unicode(7), nullable=True),
    Column('css', UnicodeText(), nullable=True),
    Column('frozen', Boolean, default=False),
    Column('milestones', Boolean, default=False),
    Column('use_norms', Boolean, nullable=True, default=True),
    Column('require_selection', Boolean, nullable=True, default=False),
    Column('is_authenticated', Boolean, nullable=True, default=False),
    Column('hide_global_categories', Boolean, nullable=True, default=False),
    Column('editable_comments_default', Boolean, nullable=True, default=True),
    Column('require_valid_email', Boolean, nullable=True, default=True),
)

badge_table = Table(
    'badge', metadata,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('type', String(40), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id',
                                              ondelete="CASCADE",),
           nullable=True),
    # attributes for hierarchical badges (CategoryBadges)
    Column('select_child_description', Unicode(255), default=u'',
           nullable=False),
    Column('parent_id', Integer, ForeignKey('badge.id', ondelete="CASCADE"),
           nullable=True),
    # attributes for UserBadges
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    Column('visible', Boolean, default=True),
)

votedetail_table = Table(
    'votedetail', metadata,
    Column('instance_id', Integer,
           ForeignKey('instance.id', ondelete='CASCADE')),
    Column('badge_id', Integer,
           ForeignKey('badge.id', ondelete='CASCADE')),
)


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    votedetail_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
