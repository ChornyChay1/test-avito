from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app import schemas, models

router = APIRouter()


async def fetch_team(db: AsyncSession, team_name: str):
    result = await db.execute(
        select(models.Team)
        .options(selectinload(models.Team.members))
        .where(models.Team.team_name == team_name)
    )
    return result.scalar_one_or_none()


@router.post("/add", response_model=schemas.Team, status_code=201)
async def add_team(team: schemas.Team, db: AsyncSession = Depends(get_db)):
    existing_team = await db.execute(
        select(models.Team).where(models.Team.team_name == team.team_name)
    )
    team_obj = existing_team.scalar_one_or_none()

    if not team_obj:
        team_obj = models.Team(team_name=team.team_name)
        db.add(team_obj)

    for member in team.members:
        existing_user = await db.get(models.User, member.user_id)
        if existing_user:
            existing_user.team_name = team.team_name
            existing_user.username = member.username
            existing_user.is_active = member.is_active
        else:
            new_user = models.User(
                user_id=member.user_id,
                username=member.username,
                is_active=member.is_active,
                team=team_obj,
            )
            db.add(new_user)

    await db.commit()
    await db.refresh(team_obj)
    return schemas.Team(
        team_name=team_obj.team_name,
        members=[
            schemas.TeamMember(
                user_id=m.user_id, username=m.username, is_active=m.is_active
            )
            for m in team_obj.members
        ],
    )


@router.get("/get", response_model=schemas.Team)
async def get_team(team_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Team)
        .options(selectinload(models.Team.members))
        .where(models.Team.team_name == team_name)
    )
    team_obj = result.scalar_one_or_none()
    if not team_obj:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": "resource not found"}
            },
        )

    return schemas.Team(
        team_name=team_obj.team_name,
        members=[
            schemas.TeamMember(
                user_id=m.user_id, username=m.username, is_active=m.is_active
            )
            for m in team_obj.members
        ],
    )


@router.post("/team/deactivate")
async def deactivate_team_users(
    team_name: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Team)
        .where(models.Team.team_name == team_name)
        .options(selectinload(models.Team.members))
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    for user in team.members:
        user.is_active = False

    open_prs = await db.execute(
        select(models.PullRequest)
        .where(models.PullRequest.status == "OPEN")
        .options(selectinload(models.PullRequest.assigned_reviewers))
    )
    for pr in open_prs.scalars():
        pr.assigned_reviewers = [
            u for u in pr.assigned_reviewers if u.is_active
        ]

    await db.commit()
    return {
        "status": "OK",
        "deactivated_users": [u.user_id for u in team.members],
    }
