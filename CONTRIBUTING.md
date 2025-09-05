# Contributing to DocLink Doctor

Thank you for your interest in contributing to DocLink Doctor! 🔗

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DocLink-Doctor.git
   cd DocLink-Doctor
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest tests/ -v
   ```

4. Run linting:
   ```bash
   ruff check src/
   black src/ --check
   ```

5. Commit with conventional commits:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve issue"
   git commit -m "docs: update documentation"
   ```

## Code Style

- Use Black for formatting
- Follow PEP 8 guidelines
- Add type hints to new functions
- Write docstrings for public APIs

## Testing

- All new features need tests
- Maintain test coverage above 80%
- Use `responses` library for mocking HTTP requests

## Pull Request Process

1. Update README.md if needed
2. Update CHANGELOG.md
3. Ensure all tests pass
4. Request review from maintainers

## Questions?

Open an issue for discussion!
