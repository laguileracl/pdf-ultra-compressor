.PHONY: format lint test smoke wiki-sync

format:
	black .
	ruff format .

lint:
	ruff .
	ruff format --check .

smoke:
	python ci/smoke_test.py

wiki-sync:
	bash scripts/wiki_sync.sh
