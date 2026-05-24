# Contributing to Kaginet

We welcome contributions to the open-source integration layer: framework adapters, documentation, examples, and verification tools.

## What You Can Contribute

- **New framework adapters** (e.g., OpenAI Agents SDK, Vercel AI SDK, AutoGen)
- **Documentation improvements** (typos, clarifications, new guides)
- **Example code** (integration patterns, use cases)
- **Bug reports** for adapters or documentation
- **Feature requests** for the public API

## What Lives Elsewhere

The ICS server (Rust), dashboard, and MCP server are not part of this repository. Bug reports and feature requests for those components are welcome as GitHub issues, but code contributions target the adapters and docs.

## Development Setup

### Adapter Development

```bash
# Clone the repo
git clone https://github.com/kaginet/kaginet.git
cd kaginet

# Install LangChain adapter in dev mode
cd adapters/langchain
pip install -e ".[dev]"

# Install CrewAI adapter in dev mode
cd ../crewai
pip install -e ".[dev]"

# Run tests (no API key needed, all tests use mocks)
cd ..
pytest tests/ -v
```

### Writing a New Adapter

1. Create a new directory under `adapters/your-framework/`
2. Implement tools that call the ICS REST API (see `adapters/langchain/_http.py` for the HTTP helper pattern)
3. Add tests with mocked responses (see `adapters/tests/conftest.py` for mock fixtures)
4. Add a `pyproject.toml` with proper metadata
5. Submit a PR

### Documentation

Documentation lives in `docs/`. We use standard Markdown with Mermaid diagrams for architecture visuals.

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Ensure all tests pass: `pytest adapters/tests/ -v`
4. Update documentation if your change affects the public API
5. Submit a PR with a clear description

## Code Style

- Python: follow the existing style (type hints, docstrings, no star imports)
- Markdown: one sentence per line, no trailing whitespace
- No hardcoded URLs or API keys in code (use environment variables)

## License

By contributing, you agree that your contributions will be licensed under the terms specified in [LICENSE](LICENSE).
