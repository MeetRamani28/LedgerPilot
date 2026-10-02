from fastapi import APIRouter
from app.api.v1.endpoints import invoices, events, audit_logs

api_router = APIRouter()
api_router.include_router(invoices.router)
api_router.include_router(events.router)
api_router.include_router(audit_logs.router)
