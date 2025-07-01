# Policy Enforcer Makefile

.PHONY: help test test-unit test-integration test-legacy test-coverage clean install setup

help:
	@echo "Policy Enforcer Development Commands:"
	@echo ""
	@echo "  setup           - Set up development environment"
	@echo "  install         - Install dependencies"
	@echo "  test            - Run unit tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration- Run integration tests (requires API key)"
	@echo "  test-legacy     - Run legacy tests"
	@echo "  test-coverage   - Run tests with coverage report"
	@echo "  clean           - Clean up generated files"
	@echo ""

setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "Setup complete! Activate with: source venv/bin/activate"

install:
	./venv/bin/pip install -r requirements.txt

test: test-unit

test-unit:
	./venv/bin/python -m pytest tests/unit -v

test-integration:
	./venv/bin/python -m pytest tests/integration -v

test-legacy:
	./venv/bin/python -m pytest tests/legacy -v

test-coverage:
	./venv/bin/python run_tests.py

test-all:
	./venv/bin/python run_tests.py --all

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development shortcuts
dev-setup: setup
	@echo "Development environment ready!"

dev-test: test-coverage
	@echo "Opening coverage report..."
	@which open > /dev/null && open htmlcov/index.html || echo "Coverage report: htmlcov/index.html"