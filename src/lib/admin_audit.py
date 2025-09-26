from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from src.models.models import AdminAudit


@dataclass
class AdminAuditPayload:
    action: str
    actor_email: str | None
    target_type: str | None = None
    target_id: str | None = None
    summary: str | None = None
    detail: str | None = None
    ip_address: str | None = None
    extra: dict[str, Any] | None = None


def record_admin_audit(session: Session, payload: AdminAuditPayload) -> None:
    """Persist an AdminAudit record.

    extra is merged into detail (JSON-ish string) if provided.
    """
    detail = payload.detail
    if payload.extra:
        import json

        blob = {"detail": detail, **payload.extra}
        detail = json.dumps(blob, separators=(",", ":"))[:2000]
    audit = AdminAudit(
        action=payload.action,
        actor_email=payload.actor_email,
        target_type=payload.target_type,
        target_id=payload.target_id,
        summary=payload.summary,
        detail=detail,
        ip_address=payload.ip_address,
    )
    session.add(audit)


__all__ = ["record_admin_audit", "AdminAuditPayload"]
