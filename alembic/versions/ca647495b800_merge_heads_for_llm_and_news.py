"""merge heads for llm and news

Revision ID: ca647495b800
Revises: 20250706015740, add_llm_analysis_fields
Create Date: 2025-07-07 14:35:16.779440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca647495b800'
down_revision: Union[str, None] = ('20250706015740', 'add_llm_analysis_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
