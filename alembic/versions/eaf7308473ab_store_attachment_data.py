"""store attachment data

Revision ID: eaf7308473ab
Revises: bb999ccf3cf0
Create Date: 2022-02-19 09:16:35.544961

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'eaf7308473ab'
down_revision = 'bb999ccf3cf0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('data_uri', sa.String(), nullable=False),
        sa.Column('law_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['law_id'], ['laws.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attachments_law_id'), 'attachments', ['law_id'], unique=False)

    op.drop_column('laws', 'attachment_names')


def downgrade():
    op.add_column('laws', sa.Column('attachment_names', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_attachments_law_id'), table_name='attachments')
    op.drop_table('attachments')
