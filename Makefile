.PHONY: install dev test build deploy clean

install:
	pip install -r requirements.txt

dev:
	docker-compose up -d postgres redis
	python -m orchestrator.main --trigger weekly_review

test:
	pytest tests/ -v

build:
	docker build -t ai-company/orchestrator:latest .

deploy:
	docker-compose up -d

clean:
	docker-compose down -v
	rm -rf __pycache__ .pytest_cache

backup:
	bash scripts/backup.sh

logs:
	docker-compose logs -f orchestrator
