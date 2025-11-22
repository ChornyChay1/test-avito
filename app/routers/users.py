from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app import crud, schemas
from sqlalchemy import text

router = APIRouter()


@router.post("/setIsActive", response_model=schemas.User)
async def set_is_active(payload: dict, db: AsyncSession = Depends(get_db)):
    user_id = payload.get("user_id")
    is_active = payload.get("is_active")
    if user_id is None or is_active is None:
        raise HTTPException(
            status_code=400, detail="user_id and is_active required"
        )

    user = await crud.set_user_active(db, user_id, is_active)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": "resource not found"}
            },
        )

    return schemas.User(
        user_id=user.user_id,
        username=user.username,
        team_name=user.team_name,
        is_active=user.is_active,
    )


@router.get("/getReview")
async def get_user_reviews(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = text(
        """
        SELECT pr.pull_request_id, pr.pull_request_name, pr.author_id, pr.status
        FROM pull_requests pr
        JOIN pr_reviewers r ON pr.pull_request_id = r.pr_id
        WHERE r.user_id = :uid
    """
    )
    result = await db.execute(stmt, {"uid": user_id})
    prs = result.all()
    return {
        "user_id": user_id,
        "pull_requests": [
            schemas.PullRequestShort(
                pull_request_id=p.pull_request_id,
                pull_request_name=p.pull_request_name,
                author_id=p.author_id,
                status=p.status,
            )
            for p in prs
        ],
    }
