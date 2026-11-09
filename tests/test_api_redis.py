"""Тот же сценарий на Redis. Запускается, только если задан REDIS_URL (в CI — сервис redis)."""
import os

import pytest
from fastapi.testclient import TestClient

from services.gamification_api.app import RedisStore, app

pytestmark = pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="REDIS_URL не задан")


def test_xp_and_leaderboard_persist_in_redis():
    import redis
    redis.from_url(os.environ["REDIS_URL"]).flushdb()
    app.state.store = RedisStore(os.environ["REDIS_URL"])
    with TestClient(app) as c:
        for _ in range(2):
            c.post("/events/submission", json={"user_id": "r1", "task_id": "q20", "solved": True, "attempts": 1})
        board = c.get("/leaderboard").json()
    assert board[0]["user_id"] == "r1" and board[0]["xp"] > 0
