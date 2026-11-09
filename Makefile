PY ?= python

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -v

simulate:
	$(PY) -m simulation.simulate --seed 42 --reps 5 --out bench/results/simulation.csv

micro:
	$(PY) -m bench.micro

up:
	docker compose up -d --build

load:          # сервис должен быть запущен (make up)
	$(PY) -m bench.load --label $(STORE) --reps 3

report:
	$(PY) -m bench.report

.PHONY: install test simulate micro up load report
