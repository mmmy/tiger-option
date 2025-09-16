.PHONY: help install install-dev clean test test-cov lint format type-check run dev build docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  clean        - Clean up cache and build files"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black, isort)"
	@echo "  type-check   - Run type checking (mypy)"
	@echo "  run          - Run the application"
	@echo "  dev          - Run the application in development mode"
	@echo "  build        - Build the package"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 src/ tests/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Development
run:
	python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Build
build:
	python -m build

# Docker
docker-build:
	docker build -t tiger-options-trading .

docker-run:
	docker run -p 8000:8000 tiger-options-trading

# All quality checks
check: lint type-check test

# Setup development environment
setup-dev: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make dev' to start the development server"
