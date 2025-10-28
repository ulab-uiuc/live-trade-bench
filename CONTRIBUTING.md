# Contributing to Live Trade Bench

We welcome contributions to Live Trade Bench! This document provides guidelines for contributing to the project.

## Getting Started

For detailed information about contributing, please contact: **haofeiy2@illinois.edu**

## Basic Rules

### Code Style

- Follow [PEP 8](https://pep8.org/) style guide for Python code
- Use [Black](https://github.com/psf/black) for code formatting: `poetry run black .`
- Use type hints where applicable
- Write descriptive commit messages

### Testing

- Add tests for new features
- Ensure all tests pass before submitting: `poetry run pytest tests/`
- Maintain or improve code coverage

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and commit: `git commit -m "Add: description of your changes"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request with a clear description

### Commit Message Format

- **Add**: New features or files
- **Fix**: Bug fixes
- **Update**: Changes to existing features
- **Refactor**: Code restructuring without changing functionality
- **Docs**: Documentation changes
- **Test**: Adding or updating tests

### Code Review

- All submissions require review before merging
- Address reviewer feedback promptly
- Keep PRs focused on a single feature or fix

## Questions?

If you have any questions or need clarification, please reach out to **haofeiy2@illinois.edu**.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (PolyForm Noncommercial License 1.0.0).

