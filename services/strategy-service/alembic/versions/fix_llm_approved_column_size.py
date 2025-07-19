"""fix llm_approved column size

Revision ID: fix_llm_approved_column_size
Revises: add_llm_analysis_fields
Create Date: 2025-07-08 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'fix_llm_approved_column_size'
down_revision: Union[str, None] = 'add_llm_analysis_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get connection to execute raw SQL
    connection = op.get_bind()
    
    # Fix llm_approved column size from VARCHAR(5) to VARCHAR(10)
    try:
        connection.execute(text("ALTER TABLE backtest_trades ALTER COLUMN llm_approved TYPE VARCHAR(10)"))
        print("✅ Successfully updated llm_approved column size to VARCHAR(10)")
    except Exception as e:
        print(f"⚠️  Warning: Could not update llm_approved column: {e}")
        # Column might already be the right size or not exist


def downgrade() -> None:
    # Get connection to execute raw SQL
    connection = op.get_bind()
    
    # Revert llm_approved column size back to VARCHAR(5)
    try:
        connection.execute(text("ALTER TABLE backtest_trades ALTER COLUMN llm_approved TYPE VARCHAR(5)"))
        print("✅ Successfully reverted llm_approved column size to VARCHAR(5)")
    except Exception as e:
        print(f"⚠️  Warning: Could not revert llm_approved column: {e}") 