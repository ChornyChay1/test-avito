from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Enum,
    Table,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class PRStatus(str, enum.Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


class Team(Base):
    __tablename__ = "teams"
    team_name = Column(String, primary_key=True)
    members = relationship("User", back_populates="team", lazy="selectin")


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    team_name = Column(String, ForeignKey("teams.team_name"))
    is_active = Column(Boolean, default=True)
    team = relationship("Team", back_populates="members", lazy="selectin")


pr_reviewers = Table(
    "pr_reviewers",
    Base.metadata,
    Column("pr_id", String, ForeignKey("pull_requests.pull_request_id")),
    Column("user_id", String, ForeignKey("users.user_id")),
)


class PullRequest(Base):
    __tablename__ = "pull_requests"
    pull_request_id = Column(String, primary_key=True)
    pull_request_name = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    status = Column(Enum(PRStatus), default=PRStatus.OPEN)
    assigned_reviewers = relationship(
        "User", secondary=pr_reviewers, lazy="selectin"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    merged_at = Column(DateTime(timezone=True), nullable=True)
