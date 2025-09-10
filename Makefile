.PHONY: format lint test smoke wiki-sync benchmark generate-samples

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

benchmark:
	python benchmarks/benchmark_runner.py

generate-samples:
	python benchmarks/generate_samples.py
