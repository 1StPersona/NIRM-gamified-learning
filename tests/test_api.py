"""Интеграционный тест сервиса на хранилище в памяти."""
from fastapi.testclient import TestClient

from services.gamification_api.app import MemoryStore, app


def client() -> TestClient:
    app.state.store = MemoryStore()
    return TestClient(app)


def test_solved_submission_awards_xp_and_updates_rating():
    c = client()
    r = c.post("/events/submission", json={"user_id": "u1", "task_id": "q25", "solved": True, "attempts": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["xp_gained"] > 0 and body["theta"] > 0
    assert body["next_task"] in {f"q{i:02d}" for i in range(50)}


def test_failed_submission_gives_no_xp():
    c = client()
    body = c.post("/events/submission", json={"user_id": "u2", "task_id": "q25", "solved": False, "attempts": 3}).json()
    assert body["xp_gained"] == 0 and body["theta"] < 0


def test_leaderboard_is_sorted_by_xp():
    c = client()
    for uid, n in [("a", 1), ("b", 3), ("c", 2)]:
        for _ in range(n):
            c.post("/events/submission", json={"user_id": uid, "task_id": "q10", "solved": True, "attempts": 1})
    assert [row["user_id"] for row in c.get("/leaderboard").json()] == ["b", "c", "a"]


def test_invalid_event_rejected():
    assert client().post("/events/submission", json={"user_id": "", "task_id": "q1", "solved": True, "attempts": 0}).status_code == 422
