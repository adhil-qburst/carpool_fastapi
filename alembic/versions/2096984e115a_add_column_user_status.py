from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f007e60ce439"
down_revision: Union[str, Sequence[str], None] = "eb5a16cfb02e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_status = sa.Enum(
        "pending",
        "active",
        "disabled",
        name="user_status",
    )

    # IMPORTANT: create enum before using it
    user_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "status",
            user_status,
            server_default="pending",
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_email_verified")
    op.drop_column("users", "status")

    user_status = sa.Enum(
        "pending",
        "active",
        "disabled",
        name="user_status",
    )

    # Remove enum after the column is removed
    user_status.drop(op.get_bind(), checkfirst=True)
