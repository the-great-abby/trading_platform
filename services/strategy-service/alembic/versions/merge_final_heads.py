"""merge final heads

Revision ID: merge_final_heads_001
Revises: 20250710_add_options_contracts_cache, fix_llm_approved_column_size
Create Date: 2024-07-10 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_final_heads_001'
down_revision = ('20250710_add_options_contracts_cache', 'fix_llm_approved_column_size')
branch_labels = None
depends_on = None


def upgrade():
    # This is a merge migration - no schema changes needed
    # All schema changes are already applied
    pass


def downgrade():
    # This is a merge migration - no schema changes needed
    pass 