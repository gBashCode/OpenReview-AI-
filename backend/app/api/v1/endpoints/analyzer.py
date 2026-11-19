"""Pull Request Analysis API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.schemas import PRAnalysisRequest, PRAnalysisResult
from app.analyzer.service import AnalyzerService
from app.database.session import get_db

router = APIRouter(prefix="/analyzer", tags=["PR Analyzer"])


def get_analyzer_service(session: AsyncSession = Depends(get_db)) -> AnalyzerService:
    return AnalyzerService(session)


@router.post(
    "/diff",
    response_model=PRAnalysisResult,
    summary="Analyze ad-hoc unified Git diff with change detection and risk scoring",
)
async def analyze_diff(
    payload: PRAnalysisRequest,
    repository_id: Optional[str] = Query(None, description="Optional repository ID for context cross-referencing"),
    service: AnalyzerService = Depends(get_analyzer_service),
) -> PRAnalysisResult:
    return await service.analyze_raw_diff(
        raw_diff=payload.raw_diff or "",
        title=payload.title or "Pull Request Diff",
        description=payload.description or "",
        repository_id=repository_id,
    )
