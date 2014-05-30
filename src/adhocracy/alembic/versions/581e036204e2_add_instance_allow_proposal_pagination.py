"""add instance.allow_proposal_pagination

Revision ID: 581e036204e2
Revises: 486aab29697a
Create Date: 2014-05-30 17:32:06.053907

"""

# revision identifiers, used by Alembic.
revision = '581e036204e2'
down_revision = '486aab29697a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('instance', sa.Column('allow_proposal_pagination', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('instance', 'allow_proposal_pagination')
