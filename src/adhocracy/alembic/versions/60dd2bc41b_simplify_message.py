"""simplify_message

Revision ID: 60dd2bc41b
Revises: None
Create Date: 2014-02-04 21:35:56.943445

"""

# revision identifiers, used by Alembic.
revision = '60dd2bc41b'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('message', sa.Column('instance_id', sa.INTEGER(), nullable=True))
    op.drop_column('message', 'sender_name')
    op.drop_column('message', 'sender_email')
    op.drop_column('message', 'include_footer')


def downgrade():
    op.add_column('message', sa.Column('include_footer', sa.Boolean(), nullable=False))
    op.add_column('message', sa.Column('sender_email', sa.Unicode(length=255), nullable=False))
    op.add_column('message', sa.Column('sender_name', sa.Unicode(length=255), nullable=True))
    op.drop_column('message', 'instance_id')
