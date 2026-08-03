"""API router aggregator — registers all v1 sub-routers under a single prefix.

Each sub-router is mounted here exactly once. Adding a new domain router
means adding two lines in this file only — the rest of the app is untouched.
"""

from fastapi import APIRouter
from src.api.v1 import auth, competitors, monitoring, reports
from src.domains.snapshots import routes as snapshot_routes

api_router = APIRouter()

# Register sub-routers under version 1 prefix
api_router.include_router(auth.router)  # prefix="/auth" is set inside auth.py
api_router.include_router(competitors.router, prefix="/competitors", tags=["Competitors"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring Schedules"])
api_router.include_router(reports.router, prefix="/reports", tags=["Intelligence Reports"])
api_router.include_router(snapshot_routes.router, prefix="", tags=["Monitoring"])
