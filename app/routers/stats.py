from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app import models

router = APIRouter()


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result_users = await db.execute(
        select(models.User.user_id, func.count(models.pr_reviewers.c.pr_id))
        .outerjoin(
            models.pr_reviewers,
            models.User.user_id == models.pr_reviewers.c.user_id,
        )
        .group_by(models.User.user_id)
    )
    users_stats = {row.user_id: row[1] for row in result_users.all()}

    result_prs = await db.execute(
        select(
            models.PullRequest.pull_request_id,
            func.count(models.pr_reviewers.c.user_id),
        )
        .outerjoin(
            models.pr_reviewers,
            models.PullRequest.pull_request_id == models.pr_reviewers.c.pr_id,
        )
        .group_by(models.PullRequest.pull_request_id)
    )
    prs_stats = {row.pull_request_id: row[1] for row in result_prs.all()}

    return {"users": users_stats, "pull_requests": prs_stats}


@router.get("/health")
async def health():
    return {"status": "ok"}
