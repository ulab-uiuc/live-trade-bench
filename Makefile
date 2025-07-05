.PHONY: help install dev test lint format auto-lint clean demo

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Install development dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  auto-lint  - Auto-fix all format and lint issues"
	@echo "  clean      - Clean cache files"
	@echo "  demo       - Run demo script"

# Install core dependencies
install:
	pip install -r requirements.txt
	pip install -e .

# Install development dependencies (includes all deps)
dev: install
	@echo "Development environment setup complete"

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	ruff check .

# Format code
format:
	ruff format .

# Auto-fix all format and lint issues
auto-lint:
	@echo "🔧 Auto-fixing all format and lint issues..."
	@echo "📝 Formatting code with ruff..."
	ruff format .
	@echo "🔍 Running linting with auto-fix..."
	ruff check --fix .
	@echo "✅ Auto-lint completed! All fixable issues have been resolved."
	@echo "💡 Run 'make lint' to check for any remaining issues."

# Clean cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Run demo
demo:
	@echo "Running demo script..."
	@chmod +x scripts/demo.sh
	@cd scripts && ./demo.sh

# Test metrics system
test-metrics:
	@echo "Testing metrics system..."
	@python examples/test_metrics.py

# Test visualization system
test-visualization:
	@echo "Testing visualization system..."
	@python examples/test_visualization.py

# Setup pre-commit hooks
setup-hooks:
	pre-commit install
	pre-commit install --hook-type pre-push

# Full development setup
setup: install setup-hooks
	@echo "Development environment fully configured" 