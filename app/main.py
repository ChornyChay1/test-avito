from fastapi import FastAPI
from app.routers import teams, users, pull_requests, stats

app = FastAPI(title="PR Reviewer Assignment Service")


app.include_router(stats.router)
app.include_router(teams.router, prefix="/team")
app.include_router(users.router, prefix="/users")
app.include_router(pull_requests.router, prefix="/pullRequest")
