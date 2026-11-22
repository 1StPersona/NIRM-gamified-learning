PY ?= python

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -v

simulate:
	$(PY) -m simulation.simulate --seed 42 --reps 5 --out bench/results/simulation.csv

policies:
	$(PY) -m simulation.policies --seed 42 --reps 5
	$(PY) -m simulation.policies --seed 42 --reps 5 --variant misspec
	$(PY) -m simulation.policies --seed 42 --reps 5 --variant warm

analyze:
	$(PY) -m analysis.preliminary

micro:
	$(PY) -m bench.micro

up:
	docker compose up -d --build

load:          # сервис должен быть запущен (make up)
	$(PY) -m bench.load --label $(STORE) --reps 3

report:
	$(PY) -m bench.report

.PHONY: install test simulate policies analyze micro up load report
