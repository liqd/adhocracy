from datetime import datetime

from sqlalchemy import *
from migrate import *

meta = MetaData()

user_table = Table('user', meta,
    Column('id', Integer, primary_key=True),
    Column('user_name', Unicode(255), nullable=False, unique=True, index=True),
    Column('display_name', Unicode(255), nullable=True, index=True),
    Column('bio', UnicodeText(), nullable=True),
    Column('email', Unicode(255), nullable=True, unique=False),
    Column('email_priority', Integer, default=3),
    Column('activation_code', Unicode(255), nullable=True, unique=False),
    Column('reset_code', Unicode(255), nullable=True, unique=False),
    Column('password', Unicode(80), nullable=False),
    Column('locale', Unicode(7), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime)
    )


openid_table = Table('openid', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('identifier', Unicode(255), nullable=False, index=True) 
    )


oid_nonces = Table('oid_nonces', meta,
    Column('server_url', LargeBinary, nullable=False),
    Column('timestamp', Integer, primary_key=True),
    Column('salt', Unicode(40), nullable=False, index=True)
    )

    
oid_associations = Table('oid_associations', meta,
    Column('server_url', LargeBinary, nullable=False),
    Column('handle', Unicode(255), nullable=False, index=True),
    Column('secret', LargeBinary, nullable=False),
    Column('issued', Integer, primary_key=True),
    Column('lifetime', Integer, primary_key=True),
    Column('assoc_type', Unicode(64), nullable=False)
    )

twitter_table = Table('twitter', meta, 
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('twitter_id', Integer),
    Column('key', Unicode(255), nullable=False),
    Column('secret', Unicode(255), nullable=False),
    Column('screen_name', Unicode(255), nullable=False),
    Column('priority', Integer, default=4)
    )

group_table = Table('group', meta, 
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False, unique=True),
    Column('code', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
    )

group_permission_table = Table('group_permission', meta,
    Column('group_id', Integer, ForeignKey('group.id',
           onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permission.id',
           onupdate="CASCADE", ondelete="CASCADE"))
    )

permission_table = Table('permission', meta,
    Column('id', Integer, primary_key=True),
    Column('permission_name', Unicode(255), nullable=False, unique=True)
    )

category_graph = Table('category_graph', meta,
    Column('parent_id', Integer, ForeignKey('delegateable.id')),
    Column('child_id', Integer, ForeignKey('delegateable.id'))
    )

delegateable_table = Table('delegateable', meta,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )

issue_table = Table('issue', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

delegation_table = Table('delegation', meta,                      
    Column('id', Integer, primary_key=True),
    Column('agent_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('principal_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('revoke_time', DateTime, default=None, nullable=True)
    )

proposal_table = Table('proposal', meta,
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

alternative_table = Table('alternative', meta, 
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('left_id', Integer, ForeignKey('proposal.id'), nullable=False),
    Column('right_id', Integer, ForeignKey('proposal.id'), nullable=False)
    )

dependency_table = Table('dependency', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False),
    Column('requirement_id', Integer, ForeignKey('proposal.id'), nullable=False)
    )

poll_table = Table('poll', meta,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
    )

vote_table = Table('vote', meta, 
    Column('id', Integer, primary_key=True),
    Column('orientation', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('poll_id', Integer, ForeignKey('poll.id'), nullable=False),
    Column('delegation_id', Integer, ForeignKey('delegation.id'), nullable=True)
    )

revision_table = Table('revision', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('text', UnicodeText(), nullable=False),
    Column('sentiment', Integer, default=0),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False)
    )

comment_table = Table('comment', meta,                  
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, default=None, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('topic_id', Integer, ForeignKey('delegateable.id'), nullable=False),
    Column('canonical', Boolean, default=False),
    Column('reply_id', Integer, ForeignKey('comment.id'), nullable=True)
    )

instance_table = Table('instance', meta,
    Column('id', Integer, primary_key=True),
    Column('key', Unicode(20), nullable=False, unique=True),
    Column('label', Unicode(255), nullable=False),
    Column('description', UnicodeText(), nullable=True),
    Column('required_majority', Float, nullable=False),
    Column('activation_delay', Integer, nullable=False),
    Column('create_time', DateTime, default=func.now()),
    Column('access_time', DateTime, default=func.now(), onupdate=func.now()),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('default_group_id', Integer, ForeignKey('group.id'), nullable=True)    
    )

membership_table = Table('membership', meta, 
    Column('id', Integer, primary_key=True),
    Column('approved', Boolean, nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('expire_time', DateTime, nullable=True),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False)
    )

karma_table = Table('karma', meta,
    Column('id', Integer, primary_key=True),
    Column('value', Integer, nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('comment_id', Integer, ForeignKey('comment.id'), nullable=False),
    Column('donor_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False)     
    )

watch_table = Table('watch', meta,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('entity_type', Unicode(255), nullable=False, index=True),
    Column('entity_ref', Unicode(255), nullable=False, index=True)                
    )

event_topic_table = Table('event_topic', meta,
    Column('event_id', Integer, ForeignKey('event.id',
           onupdate="CASCADE", ondelete="CASCADE")),
    Column('topic_id', Integer, ForeignKey('delegateable.id',
           onupdate="CASCADE", ondelete="CASCADE"))
    )


event_table = Table('event', meta, 
    Column('id', Integer, primary_key=True),
    Column('event', Unicode(255), nullable=False),
    Column('time', DateTime, default=datetime.utcnow),
    Column('data', UnicodeText(), nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True)
    )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    user_table.create()
    openid_table.create()
    oid_nonces.create()
    oid_associations.create()
    twitter_table.create()
    group_table.create()
    group_permission_table.create()
    permission_table.create()
    category_graph.create()
    delegateable_table.create()
    issue_table.create()
    delegation_table.create()
    proposal_table.create()
    alternative_table.create()
    dependency_table.create()
    poll_table.create()
    vote_table.create()
    revision_table.create()
    comment_table.create()
    instance_table.create()
    membership_table.create()
    karma_table.create()
    watch_table.create()
    event_topic_table.create()
    event_table.create()

def downgrade(migrate_engine):
    raise NotImplementedError()



