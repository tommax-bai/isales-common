"""add provider_credential table + encrypt existing callback_config.signing_secret

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-23 19:30:00.000000

Spec: openspec/changes/impl-provider-credential-db-ssot — capability
``provider-credential``. Additive: new ``provider_credential`` table; existing
``callback_config.signing_secret`` is already a Text column, but any rows that
hold plaintext (legacy / dev-seeded) get one-time encrypted in place.

The Fernet master key MUST be set in env ``ISALES_FERNET_KEY`` before this
migration runs; otherwise the signing_secret one-time-encrypt step skips
(plaintext rows survive, callers see decrypt errors at runtime). Fresh
deployments have an empty callback_config so the encrypt step is a no-op.
"""
from __future__ import annotations

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Fernet urlsafe-base64 tokens always start with 'gAAAA' (version byte 0x80
# = 'g' under urlsafe_b64encode + 3 zero bytes preface). Use this as a cheap
# idempotency check when batch-encrypting existing rows.
FERNET_TOKEN_PREFIX = "gAAAA"


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Create provider_credential.
    op.create_table(
        "provider_credential",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("provider_id", sa.String(length=32), nullable=False),
        sa.Column("field_name", sa.String(length=32), nullable=False),
        sa.Column("cipher_text", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_credential")),
        sa.UniqueConstraint(
            "provider_id",
            "field_name",
            name="uq_provider_credential_provider_field",
        ),
    )
    op.create_index(
        op.f("ix_provider_credential_provider_id"),
        "provider_credential",
        ["provider_id"],
    )

    # 2) One-time encrypt any plaintext callback_config.signing_secret rows.
    #    Skip silently if ISALES_FERNET_KEY is not configured at migration
    #    time (fresh deploys have no rows to migrate anyway).
    if not os.environ.get("ISALES_FERNET_KEY"):
        return

    from isales_common.utils.crypto import encrypt  # local import; avoids
                                                    # alembic env coupling

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, signing_secret FROM callback_config "
            "WHERE signing_secret IS NOT NULL "
            f"  AND signing_secret NOT LIKE '{FERNET_TOKEN_PREFIX}%'"
        )
    ).fetchall()
    for row in rows:
        cipher = encrypt(row.signing_secret)
        conn.execute(
            sa.text(
                "UPDATE callback_config SET signing_secret = :cipher "
                "WHERE id = :id"
            ),
            {"cipher": cipher, "id": row.id},
        )


def downgrade() -> None:
    """Downgrade schema.

    Decrypt any cipher signing_secret rows back to plaintext (best-effort;
    rows fail to decrypt are left as-is), then drop provider_credential.
    """
    if os.environ.get("ISALES_FERNET_KEY"):
        from isales_common.utils.crypto import CryptoError, decrypt

        conn = op.get_bind()
        rows = conn.execute(
            sa.text(
                "SELECT id, signing_secret FROM callback_config "
                "WHERE signing_secret IS NOT NULL "
                f"  AND signing_secret LIKE '{FERNET_TOKEN_PREFIX}%'"
            )
        ).fetchall()
        for row in rows:
            try:
                plain = decrypt(row.signing_secret)
            except CryptoError:
                continue
            conn.execute(
                sa.text(
                    "UPDATE callback_config SET signing_secret = :plain "
                    "WHERE id = :id"
                ),
                {"plain": plain, "id": row.id},
            )

    op.drop_index(
        op.f("ix_provider_credential_provider_id"),
        table_name="provider_credential",
    )
    op.drop_table("provider_credential")
