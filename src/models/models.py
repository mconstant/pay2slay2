from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Discord identity
    discord_user_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    discord_username: Mapped[str | None] = mapped_column(String(100))
    discord_guild_member: Mapped[bool] = mapped_column(Boolean, default=False)

    # Epic identity from Yunite
    epic_account_id: Mapped[str | None] = mapped_column(String(64), index=True)
    # Settlement cursor fields
    last_settled_kill_count: Mapped[int] = mapped_column(default=0)
    last_settlement_at: Mapped[datetime | None] = mapped_column()
    # Region & abuse flags (JSON/text for future extensibility)
    region_code: Mapped[str | None] = mapped_column(String(8))
    abuse_flags: Mapped[str | None] = mapped_column(String(500))

    # Linked wallet (ban_ address) through WalletLink
    wallet_links: Mapped[list[WalletLink]] = relationship(back_populates="user")

    accruals: Mapped[list[RewardAccrual]] = relationship(back_populates="user")
    payouts: Mapped[list[Payout]] = relationship(back_populates="user")


class AdminUser(Base, TimestampMixin):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # for simplicity store hashed secret outside scope here
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)


class WalletLink(Base, TimestampMixin):
    __tablename__ = "wallet_links"
    __table_args__ = (
        UniqueConstraint("user_id", "address", name="uq_wallet_per_user"),
        Index("ix_wallet_address", "address"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    address: Mapped[str] = mapped_column(String(70))  # ban_... up to ~64
    is_primary: Mapped[bool] = mapped_column(default=True)
    verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[datetime | None] = mapped_column()

    user: Mapped[User] = relationship(back_populates="wallet_links")


class VerificationRecord(Base, TimestampMixin):
    __tablename__ = "verification_records"
    __table_args__ = (
        Index("ix_verif_discord", "discord_user_id"),
        Index("ix_verif_epic", "epic_account_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    discord_user_id: Mapped[str] = mapped_column(String(30))
    discord_guild_member: Mapped[bool] = mapped_column(default=False)
    epic_account_id: Mapped[str | None] = mapped_column(String(64))

    source: Mapped[str] = mapped_column(String(32))  # e.g., "discord_oauth", "yunite_sync"
    status: Mapped[str] = mapped_column(String(32))  # e.g., "ok", "mismatch", "error"
    detail: Mapped[str | None] = mapped_column(String(500))


class RewardAccrual(Base, TimestampMixin):
    __tablename__ = "reward_accruals"
    __table_args__ = (
        Index("ix_accrual_user_created", "user_id", "created_at"),
        Index("ix_accrual_settled", "settled"),
        # Idempotency: at most one accrual per user per epoch_minute
        UniqueConstraint("user_id", "epoch_minute", name="uq_accrual_user_epoch"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # count of kills accrued since last cursor for user
    kills: Mapped[int] = mapped_column()
    # snapshot value = kills * payout_per_kill at time of accrual (BAN)
    amount_ban: Mapped[float] = mapped_column(Numeric(18, 8))
    epoch_minute: Mapped[int] = mapped_column(BigInteger)  # aggregation slot or cursor minute

    settled: Mapped[bool] = mapped_column(default=False)
    settled_at: Mapped[datetime | None] = mapped_column()
    payout_id: Mapped[int | None] = mapped_column(ForeignKey("payouts.id", ondelete="SET NULL"))

    user: Mapped[User] = relationship(back_populates="accruals")
    payout: Mapped[Payout | None] = relationship(back_populates="accruals")


class Payout(Base, TimestampMixin):
    __tablename__ = "payouts"
    __table_args__ = (
        Index("ix_payout_tx", "tx_hash", unique=True),
        Index("ix_payout_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    address: Mapped[str] = mapped_column(String(70))
    # Sum of included accruals (BAN)
    amount_ban: Mapped[float] = mapped_column(Numeric(18, 8))
    # Blockchain fields
    tx_hash: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/sent/failed
    error_detail: Mapped[str | None] = mapped_column(String(500))
    # Idempotency: hash of sorted accrual ids included in this payout
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True)
    # Retry / audit metadata
    attempt_count: Mapped[int] = mapped_column(default=1)
    first_attempt_at: Mapped[datetime | None] = mapped_column()
    last_attempt_at: Mapped[datetime | None] = mapped_column()

    user: Mapped[User] = relationship(back_populates="payouts")
    accruals: Mapped[list[RewardAccrual]] = relationship(back_populates="payout")


class AdminAudit(Base, TimestampMixin):
    __tablename__ = "admin_audit"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), index=True)
    target_type: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[str | None] = mapped_column(String(200))
    detail: Mapped[str | None] = mapped_column(String(2000))
    ip_address: Mapped[str | None] = mapped_column(String(64))


class AbuseFlag(Base, TimestampMixin):
    __tablename__ = "abuse_flags"
    __table_args__ = (Index("ix_abuse_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    flag_type: Mapped[str] = mapped_column(String(64))  # e.g., kill_rate_spike
    severity: Mapped[str] = mapped_column(String(16), default="low")  # low/med/high
    detail: Mapped[str | None] = mapped_column(String(500))
