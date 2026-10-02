"""Create the PaperDesk schema.

Revision ID: 0001_initial_schema
Revises:
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(length=50), nullable=False),
        sa.Column("last_name", sa.String(length=50), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("cash_balance", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint(
            "email = LOWER(email)",
            name="ck_users_email_lowercase",
        ),
        sa.CheckConstraint(
            "cash_balance >= 0",
            name="ck_users_cash_balance_non_negative",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "positions",
        sa.Column("position_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("number_of_shares", sa.Integer(), nullable=False),
        sa.Column("average_price_per_share", sa.Numeric(10, 2), nullable=False),
        sa.Column("last_price_per_share", sa.Numeric(10, 2), nullable=False),
        sa.Column("position_total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "number_of_shares > 0",
            name="ck_positions_number_of_shares_positive",
        ),
        sa.CheckConstraint(
            "average_price_per_share > 0",
            name="ck_positions_average_price_positive",
        ),
        sa.CheckConstraint(
            "last_price_per_share > 0",
            name="ck_positions_last_price_positive",
        ),
        sa.CheckConstraint(
            "position_total > 0",
            name="ck_positions_total_positive",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_positions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("position_id", name="pk_positions"),
    )
    op.create_index(
        "idx_positions_user_symbol",
        "positions",
        ["user_id", "symbol"],
    )

    op.create_table(
        "trades_log",
        sa.Column("trade_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("price_per_share", sa.Numeric(10, 2), nullable=False),
        sa.Column("number_of_shares", sa.Integer(), nullable=False),
        sa.Column("trade_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("trade_type", sa.String(length=4), nullable=False),
        sa.CheckConstraint(
            "number_of_shares > 0",
            name="ck_trades_log_number_of_shares_positive",
        ),
        sa.CheckConstraint(
            "price_per_share > 0",
            name="ck_trades_log_price_positive",
        ),
        sa.CheckConstraint(
            "trade_total > 0",
            name="ck_trades_log_total_positive",
        ),
        sa.CheckConstraint(
            "trade_type IN ('BUY', 'SELL')",
            name="ck_trades_log_trade_type",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_trades_log_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("trade_id", name="pk_trades_log"),
    )
    op.create_index(
        "idx_trades_log_user_executed_at",
        "trades_log",
        ["user_id", sa.text("executed_at DESC")],
    )

    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("transaction_type", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive",
        ),
        sa.CheckConstraint(
            "transaction_type IN ('DEPOSIT', 'WITHDRAW')",
            name="ck_transactions_transaction_type",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_transactions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("transaction_id", name="pk_transactions"),
    )
    op.create_index(
        "idx_transactions_user_created_at",
        "transactions",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("trades_log")
    op.drop_table("positions")
    op.drop_table("users")
