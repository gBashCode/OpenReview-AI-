"""Code Review Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_review_service
from app.schemas.review import (
    ReviewCommentCreate,
    ReviewCommentRead,
    ReviewCreate,
    ReviewDetailRead,
    ReviewRead,
)
from app.services.llm_provider_service import LLMFactory, LLMReviewSummaryOutput
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post(
    "",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or trigger a PR review pass",
)
async def create_review(
    payload: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
) -> ReviewRead:
    return await service.create_review(payload)


@router.get("/{review_id}", response_model=ReviewDetailRead, summary="Get review details & findings")
async def get_review(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
) -> ReviewDetailRead:
    return await service.get_review(review_id)


@router.post(
    "/{review_id}/comments",
    response_model=ReviewCommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an AI or human finding/comment to a review",
)
async def add_review_comment(
    review_id: str,
    payload: ReviewCommentCreate,
    service: ReviewService = Depends(get_review_service),
) -> ReviewCommentRead:
    return await service.add_finding(review_id, payload)


@router.post(
    "/{review_id}/simulate-ai-pass",
    response_model=ReviewDetailRead,
    summary="Execute multi-agent review pass simulation",
)
async def simulate_ai_pass(
    review_id: str,
    service: ReviewService = Depends(get_review_service),
) -> ReviewDetailRead:
    """Invokes the multi-agent review orchestration to inspect code and generate structured findings."""
    llm = LLMFactory.get_provider()
    result: LLMReviewSummaryOutput = await llm.generate_structured(
        prompt="Review Pull Request changes for security vulnerabilities and performance bottlenecks.",
        system_prompt="You are an expert multi-agent code review arbiter.",
        response_model=LLMReviewSummaryOutput,
    )

    for item in result.findings:
        await service.add_finding(
            review_id,
            ReviewCommentCreate(
                file_path=item.file_path,
                line_number=item.line_number,
                side="RIGHT",
                category=item.category,
                severity=item.severity,
                title=item.title,
                message=item.message,
                suggested_patch=item.suggested_patch,
            ),
        )

    await service.complete_review(
        review_id=review_id,
        summary=result.summary,
        score=result.overall_score,
        security_score=result.security_score,
        performance_score=result.performance_score,
        quality_score=result.quality_score,
    )

    return await service.get_review(review_id)
