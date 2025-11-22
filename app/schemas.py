from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class TeamMember(BaseModel):
    user_id: str
    username: str
    is_active: bool


class Team(BaseModel):
    team_name: str
    members: List[TeamMember]


class User(BaseModel):
    user_id: str
    username: str
    team_name: str
    is_active: bool


class PullRequest(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
    assigned_reviewers: List[str]
    createdAt: Optional[str]
    mergedAt: Optional[str]


class PullRequestShort(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str
    status: PRStatus
