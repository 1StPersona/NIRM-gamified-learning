#!/usr/bin/env bash
# Smoke-тест тестовой среды: сервис отвечает, событие обрабатывается, данные лежат в Redis.
set -euo pipefail
URL=${1:-http://localhost:8080}

for i in $(seq 1 30); do
  if curl -fs "$URL/health" > /dev/null; then echo "health OK (попытка $i)"; break; fi
  [ "$i" = 30 ] && { echo "сервис не поднялся за 30 с"; exit 1; }
  sleep 1
done

resp=$(curl -fs -X POST "$URL/events/submission" -H 'Content-Type: application/json' \
  -d '{"user_id":"smoke","task_id":"q25","solved":true,"attempts":1}')
echo "событие: $resp"
echo "$resp" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["xp_gained"]>0, r'

board=$(curl -fs "$URL/leaderboard?n=1")
echo "лидерборд: $board"
echo "$board" | python3 -c 'import json,sys; b=json.load(sys.stdin); assert b and b[0]["user_id"]=="smoke", b'
echo "smoke-тест пройден"
