"""Add index to speed up deleting laws

Revision ID: bb999ccf3cf0
Revises: b379bf626e54
Create Date: 2020-10-12 15:08:55.236876

"""
from alembic import op
import sqlalchemy as sa  # noqa


# revision identifiers, used by Alembic.
revision = 'bb999ccf3cf0'
down_revision = 'b379bf626e54'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_content_items_parent_id", "content_items", ["parent_id"], unique=False)


def downgrade():
    op.drop_index("ix_content_items_parent_id", table_name="content_items")
