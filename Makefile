.PHONY: setup simulate simulate-file local-stream local-stream-down test

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

simulate:
	python producer/simulator.py --drivers 50 --interval 2

simulate-sqs:
	python producer/simulator.py --sink sqs --drivers 50 --interval 2

simulate-file:
	python producer/simulator.py --sink file --drivers 50 --interval 2 --duration 300

local-stream:
	docker compose -f docker/docker-compose.yml up -d

local-stream-down:
	docker compose -f docker/docker-compose.yml down

test:
	pytest -q
