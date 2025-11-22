from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app import crud, schemas, models

router = APIRouter()


async def get_pr_with_reviewers(db: AsyncSession, pr_id: str):
    result = await db.execute(
        select(models.PullRequest)
        .options(selectinload(models.PullRequest.assigned_reviewers))
        .where(models.PullRequest.pull_request_id == pr_id)
    )
    return result.scalar_one_or_none()


@router.post("/create", response_model=schemas.PullRequest, status_code=201)
async def create_pr(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    pr_name = payload.get("pull_request_name")
    author_id = payload.get("author_id")
    if not pr_id or not pr_name or not author_id:
        raise HTTPException(
            status_code=400,
            detail="pull_request_id, pull_request_name and author_id required",
        )

    status, pr = await crud.create_pr(db, pr_id, pr_name, author_id)
    if status == "exists":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "PR_EXISTS",
                    "message": "PR id already exists",
                }
            },
        )
    if status == "author_or_team_not_found":
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "author or team not found",
                }
            },
        )

    pr = await get_pr_with_reviewers(db, pr.pull_request_id)
    if not pr:
        raise HTTPException(
            status_code=500, detail="failed to load created PR"
        )

    return {
        "pull_request_id": pr.pull_request_id,
        "pull_request_name": pr.pull_request_name,
        "author_id": pr.author_id,
        "status": (
            pr.status.value if hasattr(pr.status, "value") else pr.status
        ),
        "assigned_reviewers": [u.user_id for u in pr.assigned_reviewers],
        "createdAt": pr.created_at.isoformat() if pr.created_at else None,
        "mergedAt": pr.merged_at.isoformat() if pr.merged_at else None,
    }


@router.post("/merge", response_model=schemas.PullRequest)
async def merge_pr(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    if not pr_id:
        raise HTTPException(status_code=400, detail="pull_request_id required")

    pr = await crud.merge_pr(db, pr_id)
    if not pr:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "PR not found"}},
        )

    pr = await get_pr_with_reviewers(db, pr.pull_request_id)
    return schemas.PullRequest(
        pull_request_id=pr.pull_request_id,
        pull_request_name=pr.pull_request_name,
        author_id=pr.author_id,
        status=pr.status,
        assigned_reviewers=[u.user_id for u in pr.assigned_reviewers],
        createdAt=pr.created_at.isoformat() if pr.created_at else None,
        mergedAt=pr.merged_at.isoformat() if pr.merged_at else None,
    )


@router.post("/reassign")
async def reassign_reviewer(payload: dict, db: AsyncSession = Depends(get_db)):
    pr_id = payload.get("pull_request_id")
    old_user_id = payload.get("old_user_id") or payload.get("old_reviewer_id")
    if not pr_id or not old_user_id:
        raise HTTPException(
            status_code=400, detail="pull_request_id and old_user_id required"
        )

    status, pr, new_reviewer = await crud.reassign_reviewer(
        db, pr_id, old_user_id
    )
    if status == "pr_not_found":
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "PR or user not found",
                }
            },
        )
    if status == "merged":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "PR_MERGED",
                    "message": "cannot reassign on merged PR",
                }
            },
        )
    if status == "not_assigned":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "NOT_ASSIGNED",
                    "message": "reviewer is not assigned to this PR",
                }
            },
        )
    if status == "no_candidate":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "NO_CANDIDATE",
                    "message": "no active replacement candidate in team",
                }
            },
        )

    pr = await get_pr_with_reviewers(db, pr.pull_request_id)
    return {
        "pr": schemas.PullRequest(
            pull_request_id=pr.pull_request_id,
            pull_request_name=pr.pull_request_name,
            author_id=pr.author_id,
            status=pr.status,
            assigned_reviewers=[u.user_id for u in pr.assigned_reviewers],
            createdAt=pr.created_at.isoformat() if pr.created_at else None,
            mergedAt=pr.merged_at.isoformat() if pr.merged_at else None,
        ),
        "replaced_by": new_reviewer.user_id,
    }
