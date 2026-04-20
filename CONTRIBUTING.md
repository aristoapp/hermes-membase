# Contributing to Membase for Hermes Agent

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/aristoapp/hermes-membase.git
cd hermes-membase
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Making Changes

1. Fork the repository and create a feature branch from `main`
2. Make your changes
3. Run linting:

```bash
.venv/bin/ruff check src/
.venv/bin/ruff format --check src/
```

4. Commit with a clear message describing the change
5. Open a pull request against `main`

## Code Style

- Python 3.9+ compatible
- Formatting and linting via [Ruff](https://docs.astral.sh/ruff/)
- Type annotations on all public functions

## Testing

Run the plugin against a real Hermes install:

```bash
pip install membase-hermes
membase-hermes install
hermes
```
