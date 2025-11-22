
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_flow(async_client: AsyncClient):
    team_payload = {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": True},
            {"user_id": "u2", "username": "Bob", "is_active": True},
            {"user_id": "u3", "username": "Charlie", "is_active": True},
            {"user_id": "u4", "username": "Dave", "is_active": False},
        ],
    }

    response = await async_client.post("/team/add", json=team_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["team_name"] == "backend"
    assert len(data["members"]) == 4

    updated_payload = {
        "team_name": "backend",
        "members": [
            {"user_id": "u1", "username": "Alice", "is_active": False},
            {"user_id": "u2", "username": "Bob", "is_active": True},
            {"user_id": "u3", "username": "Charlie", "is_active": True},
            {"user_id": "u5", "username": "Eve", "is_active": True},
        ],
    }
    response = await async_client.post("/team/add", json=updated_payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data["members"]) == 5
    assert any(
        m["user_id"] == "u1" and not m["is_active"] for m in data["members"]
    )
    assert any(m["user_id"] == "u5" for m in data["members"])

    response = await async_client.get("/team/get?team_name=backend")
    assert response.status_code == 200
    assert len(response.json()["members"]) == 5

    response = await async_client.post(
        "/users/setIsActive", json={"user_id": "u3", "is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    pr_payload = {
        "pull_request_id": "pr-001",
        "pull_request_name": "Fix login",
        "author_id": "u1",
    }
    response = await async_client.post("/pullRequest/create", json=pr_payload)
    assert response.status_code == 201
    reviewers = response.json().get("assigned_reviewers", [])
    assert len(reviewers) >= 1
    assert "u2" in reviewers or "u5" in reviewers

    response = await async_client.post(
        "/pullRequest/merge", json={"pull_request_id": "pr-001"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "MERGED"

    response = await async_client.post(
        "/pullRequest/merge", json={"pull_request_id": "pr-001"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "MERGED"

    response = await async_client.post(
        "/pullRequest/reassign",
        json={"pull_request_id": "pr-001", "old_user_id": "u2"},
    )
    assert response.status_code == 409

    await async_client.post(
        "/users/setIsActive", json={"user_id": "u3", "is_active": True}
    )

    response = await async_client.post(
        "/pullRequest/create",
        json={
            "pull_request_id": "pr-003",
            "pull_request_name": "Refactor",
            "author_id": "u1",
        },
    )
    assert response.status_code == 201
    reviewers = response.json().get("assigned_reviewers", [])
    assert len(reviewers) == 2
    assert set(reviewers).issubset({"u2", "u3", "u5"})


@pytest.mark.asyncio
async def test_load_stats(async_client):
    response = await async_client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "pull_requests" in data


@pytest.mark.asyncio
async def test_e2e_team_pr_flow(async_client):
    team_payload = {
        "team_name": "qa",
        "members": [{"user_id": "u1", "username": "Alice", "is_active": True}],
    }
    response = await async_client.post("/team/add", json=team_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["team_name"] == "qa"
