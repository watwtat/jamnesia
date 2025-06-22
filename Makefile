# Jamnesia - Poker Hand Management System
# Development Makefile

.PHONY: help install test clean run dev-install lint format check coverage

# Default target
help:
	@echo "Jamnesia Development Commands"
	@echo "=============================="
	@echo "install      - Install production dependencies"
	@echo "dev-install  - Install development dependencies"
	@echo "test         - Run all tests"
	@echo "coverage     - Run tests with coverage report"
	@echo "lint         - Run code linting"
	@echo "format       - Format code with black and isort"
	@echo "check        - Run all quality checks"
	@echo "run          - Run the development server"
	@echo "clean        - Clean up temporary files"

# Installation
install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

dev-install: install
	pip install -r requirements-dev.txt

# Testing
test:
	python run_tests.py

coverage:
	coverage run run_tests.py
	coverage report
	coverage html
	@echo "HTML coverage report generated in htmlcov/"

# Code quality
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	black .
	isort .

check: lint test
	@echo "All quality checks passed!"

# Development
run:
	python app.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.db" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/