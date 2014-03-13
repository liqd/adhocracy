"""simplify_message

Revision ID: 60dd2bc41b
Revises: 79808779aa1
Create Date: 2014-02-04 21:35:56.943445

"""

# revision identifiers, used by Alembic.
revision = '60dd2bc41b'
down_revision = '79808779aa1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('message', sa.Column('instance_id', sa.INTEGER(),
                                       nullable=True))
    op.alter_column('message', 'sender_email', nullable=True)


def downgrade():
    op.alter_column('message', 'sender_email', nullable=False)
    op.drop_column('message', 'instance_id')
