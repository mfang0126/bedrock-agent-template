# Task Completion Checklist

## When Task is Complete

### 1. Code Quality (No automated tooling configured yet)
❌ **Linting**: Not configured (no ruff, flake8, pylint in pyproject.toml)
❌ **Formatting**: Not configured (no black, isort in pyproject.toml)
❌ **Type Checking**: Not configured (no mypy in pyproject.toml)

**Current State**: Project does NOT have automated linting/formatting/type checking.
**Action**: Manual code review only. Follow code_style_conventions.md patterns.

### 2. Testing
❌ **Tests**: pytest is listed as dev dependency but no tests exist yet
**Action**: Tests should be written for new features when practical

### 3. Documentation
✅ **README.md**: Keep updated with new capabilities
✅ **TECHNICAL_SPEC.md**: Update if architecture changes
✅ **Docstrings**: Ensure functions have clear docstrings

### 4. Git Workflow
✅ **Branch**: Always work on feature branches, never main
✅ **Commits**: Descriptive commit messages following conventional commits
✅ **Status**: Check `git status` before committing
✅ **Diff**: Review `git diff` before staging changes

### 5. Deployment Verification (if applicable)
- Test locally first if possible
- Document any new environment variables in .env.example
- Update setup_github_provider.py if credential changes needed
- Test end-to-end OAuth flow after deployment

### 6. Security Checks
- ✅ No hardcoded credentials in code
- ✅ All secrets in .env (local) or AWS Secrets Manager (prod)
- ✅ .env file in .gitignore
- ✅ Token handling uses @requires_access_token decorator

## Pre-Commit Checklist
- [ ] Code follows style conventions (snake_case, type hints)
- [ ] Functions have docstrings
- [ ] No print statements for debugging (only intentional logging)
- [ ] No credentials hardcoded
- [ ] Imports organized (stdlib → third-party → local)
- [ ] Manual code review (no automated linters configured)
- [ ] Git status clean (no unintended files)
- [ ] Commit message descriptive

## Future: When CI/CD is Added
This checklist should be updated when automated tooling is configured:
- Add ruff/black for formatting
- Add mypy for type checking
- Add pytest automation
- Add pre-commit hooks
