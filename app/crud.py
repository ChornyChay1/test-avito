from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from . import models
import random
from datetime import datetime


# --- Teams / Users ---
async def create_team(db: AsyncSession, team_name: str, members: list):
    team = await db.get(models.Team, team_name)
    if team:
        return None

    team = models.Team(team_name=team_name)
    db.add(team)

    for m in members:
        user = models.User(
            user_id=m["user_id"],
            username=m["username"],
            is_active=m["is_active"],
            team=team,
        )
        db.add(user)

    await db.commit()
    return team


async def set_user_active(db: AsyncSession, user_id: str, is_active: bool):
    user = await db.get(models.User, user_id)
    if not user:
        return None

    user.is_active = is_active
    await db.commit()
    return user


# --- Pull Requests ---
async def create_pr(
    db: AsyncSession, pr_id: str, pr_name: str, author_id: str
):
    pr = await db.get(models.PullRequest, pr_id)
    if pr:
        return "exists", None

    # загрузить автора вместе с его командой и её участниками
    result = await db.execute(
        select(models.User)
        .options(
            selectinload(models.User.team).selectinload(models.Team.members)
        )
        .where(models.User.user_id == author_id)
    )
    author = result.scalar_one_or_none()

    if not author or not author.team:
        return "author_or_team_not_found", None

    candidates = [
        u
        for u in author.team.members
        if u.is_active and u.user_id != author_id
    ]

    assigned = (
        random.sample(candidates, k=min(2, len(candidates)))
        if candidates
        else []
    )

    pr = models.PullRequest(
        pull_request_id=pr_id,
        pull_request_name=pr_name,
        author_id=author_id,
        status=models.PRStatus.OPEN,
        assigned_reviewers=assigned,
    )

    db.add(pr)
    await db.commit()
    return "created", pr


async def merge_pr(db: AsyncSession, pr_id: str):
    pr = await db.get(models.PullRequest, pr_id)
    if not pr:
        return None

    if pr.status == models.PRStatus.MERGED:
        return pr

    pr.status = models.PRStatus.MERGED
    pr.merged_at = datetime.utcnow()
    await db.commit()
    return pr


async def reassign_reviewer(db: AsyncSession, pr_id: str, old_user_id: str):
    result = await db.execute(
        select(models.PullRequest)
        .options(
            selectinload(models.PullRequest.assigned_reviewers)
            .selectinload(models.User.team)
            .selectinload(models.Team.members)
        )
        .where(models.PullRequest.pull_request_id == pr_id)
    )
    pr = result.scalar_one_or_none()

    if not pr:
        return "pr_not_found", None, None

    if pr.status == models.PRStatus.MERGED:
        return "merged", None, None

    old_reviewer = next(
        (u for u in pr.assigned_reviewers if u.user_id == old_user_id), None
    )
    if not old_reviewer:
        return "not_assigned", None, None

    team_members = [
        u
        for u in old_reviewer.team.members
        if u.is_active
        and u.user_id not in {r.user_id for r in pr.assigned_reviewers}
    ]

    if not team_members:
        return "no_candidate", None, None

    new_reviewer = random.choice(team_members)

    pr.assigned_reviewers.remove(old_reviewer)
    pr.assigned_reviewers.append(new_reviewer)

    await db.commit()
    return "ok", pr, new_reviewer
