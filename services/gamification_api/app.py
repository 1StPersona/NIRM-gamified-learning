"""Прототип сервиса геймификации: обработка события «решение проверено».

Хранилище: Redis (если задан REDIS_URL) или память процесса (для тестов и CI).
В полной платформе событие приходит из RabbitMQ; здесь оно принимается по REST,
чтобы сервис можно было измерять нагрузочным тестом (лекция 8).
"""
from __future__ import annotations

import os
from typing import Protocol

from fastapi import FastAPI
from pydantic import BaseModel, Field

from gamification import adaptive, progression

# Каталог квестов: 50 задач со сложностью от −2.5 до +2.4 по шкале Эло.
TASKS: dict[str, float] = {f"q{i:02d}": round(-2.5 + i * 0.1, 2) for i in range(50)}


class SubmissionEvent(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    task_id: str
    solved: bool
    attempts: int = Field(ge=1, le=100)


class SubmissionResult(BaseModel):
    xp_gained: int
    xp_total: int
    level: int
    theta: float
    next_task: str


class Store(Protocol):
    async def get_user(self, user_id: str) -> tuple[int, float]: ...
    async def save_user(self, user_id: str, xp: int, theta: float) -> None: ...
    async def get_task(self, task_id: str) -> float: ...
    async def save_task(self, task_id: str, difficulty: float) -> None: ...
    async def top(self, n: int) -> list[tuple[str, int]]: ...


class MemoryStore:
    def __init__(self) -> None:
        self.users: dict[str, tuple[int, float]] = {}
        self.tasks = dict(TASKS)

    async def get_user(self, user_id):
        return self.users.get(user_id, (0, 0.0))

    async def save_user(self, user_id, xp, theta):
        self.users[user_id] = (xp, theta)

    async def get_task(self, task_id):
        return self.tasks[task_id]

    async def save_task(self, task_id, difficulty):
        self.tasks[task_id] = difficulty

    async def top(self, n):
        return sorted(((u, v[0]) for u, v in self.users.items()), key=lambda x: -x[1])[:n]


class RedisStore:
    def __init__(self, url: str) -> None:
        import redis.asyncio as redis
        self.r = redis.from_url(url, decode_responses=True)

    async def get_user(self, user_id):
        xp, theta = await self.r.hmget(f"user:{user_id}", "xp", "theta")
        return int(xp or 0), float(theta or 0.0)

    async def save_user(self, user_id, xp, theta):
        async with self.r.pipeline(transaction=True) as p:
            p.hset(f"user:{user_id}", mapping={"xp": xp, "theta": theta})
            p.zadd("leaderboard", {user_id: xp})
            await p.execute()

    async def get_task(self, task_id):
        d = await self.r.hget("tasks", task_id)
        return float(d) if d is not None else TASKS[task_id]

    async def save_task(self, task_id, difficulty):
        await self.r.hset("tasks", task_id, difficulty)

    async def top(self, n):
        return [(u, int(s)) for u, s in await self.r.zrevrange("leaderboard", 0, n - 1, withscores=True)]


def make_store() -> Store:
    url = os.getenv("REDIS_URL")
    return RedisStore(url) if url else MemoryStore()


app = FastAPI(title="gamification-service")
app.state.store = make_store()


@app.post("/events/submission", response_model=SubmissionResult)
async def on_submission(ev: SubmissionEvent) -> SubmissionResult:
    store: Store = app.state.store
    xp, theta = await store.get_user(ev.user_id)
    difficulty = await store.get_task(ev.task_id)
    theta, difficulty = adaptive.elo_update(theta, difficulty, ev.solved)
    gained = 0
    if ev.solved:
        # опыт зависит от исходной сложности задачи, приведённой к шкале > 0
        gained = progression.xp_for_solution(max(0.5, 1.0 + difficulty / 2), ev.attempts, 0)
        xp += gained
    await store.save_user(ev.user_id, xp, theta)
    await store.save_task(ev.task_id, difficulty)
    return SubmissionResult(
        xp_gained=gained, xp_total=xp, level=progression.level_for_xp(xp),
        theta=round(theta, 4), next_task=adaptive.select_task(theta, TASKS),
    )


@app.get("/leaderboard")
async def leaderboard(n: int = 10) -> list[dict]:
    return [{"user_id": u, "xp": x} for u, x in await app.state.store.top(n)]


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
