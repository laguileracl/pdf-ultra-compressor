.PHONY: format lint test smoke

format:
	black .
	ruff format .

lint:
	ruff .
	ruff format --check .

smoke:
	python ci/smoke_test.py
