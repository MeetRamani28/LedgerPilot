from fastapi import APIRouter, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.auth import ClerkUser, get_current_user
from app.db.session import get_session
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("/")
async def list_audit_logs(
    entity_id: str = None,
    limit: int = 100,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AuditLog).where(AuditLog.user_id == current_user.user_id)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)

    result = await session.exec(stmt)
    return result.all()
