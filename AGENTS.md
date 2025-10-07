# Repository Guidelines

## Project Structure & Module Organization
The repository is being bootstrapped for the outbound GitHub authentication service. Organize runtime code under `src/`, grouping modules by domain (for example `src/providers/github/` for token exchange flows and `src/api/` for HTTP handlers). Keep shared helpers in `src/lib/`, configuration defaults in `config/`, and integration fixtures in `examples/`. Place automated tests in `tests/` mirroring the source layout (`tests/providers/test_github.py` alongside `src/providers/github.py`). Assets that support documentation or demos belong in `docs/` or `assets/` rather than the runtime tree to keep deployments lean.

## Build, Test, and Development Commands
Use the `Makefile` (or add one on first contribution) to provide a single entry point for common workflows:
- `make setup` installs dependencies declared in `requirements.txt` or `pyproject.toml` and prepares local environment variables from `.env.example`.
- `make run` launches the outbound auth service locally, watching for changes if a hot-reload wrapper is available.
- `make lint` chains formatting (e.g., `ruff`, `black`) and static analysis (`mypy`) to keep contributions clean.
- `make test` executes the full automated test suite and should pass before every push.
Expose equivalent `poetry run` or `npm run` scripts if you adopt different tooling, but keep the Make targets synchronized so new contributors have one consistent interface.

## Coding Style & Naming Conventions
Default to 4-space indentation for Python modules and follow PEP 8. Keep functions pure where feasible; reserve classes for stateful workflows such as GitHub OAuth exchanges. Name files using `snake_case`, aligning tests with `test_<unit>.py`. Configuration files (`.env`, YAML) should document every variable with inline comments. Run `ruff --fix` and `black` before committing to maintain formatting.

## Testing Guidelines
Adopt `pytest` with coverage enabled (`pytest --cov=src`). Name test modules `test_<subject>.py` and data-driven cases `test_<behavior>_<condition>`. Favor fixtures under `tests/conftest.py` for shared GitHub API stubs. Integration tests that contact external services should be marked with `@pytest.mark.integration` and skipped by default unless `CI=true`.

## Commit & Pull Request Guidelines
Use conventional commit prefixes (`feat:`, `fix:`, `chore:`) as observed in our other auth repositories. Each PR should include: a concise summary, linked issue reference (`Fixes #123`), screenshots or logs for behavioral changes, and a checklist confirming `make lint` and `make test` passed locally. Request review from a maintainer familiar with GitHub OAuth before merging.
