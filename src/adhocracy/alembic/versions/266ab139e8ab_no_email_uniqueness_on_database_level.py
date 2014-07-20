"""No email uniqueness on database level

Revision ID: 266ab139e8ab
Revises: 1e296c7f5e8c
Create Date: 2014-07-18 14:55:17.188121

"""

# revision identifiers, used by Alembic.
revision = '266ab139e8ab'
down_revision = '1e296c7f5e8c'

from alembic import op


def upgrade():
    op.drop_constraint(u'user_email_key', 'user')


def downgrade():
    op.create_unique_constraint(u'user_email_key', 'user', ['email'])
