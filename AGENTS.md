# AGENTS.md

## Project

PyChess Bot is a Python 3.10+ fork of lichess-bot. It connects the PyChess Bot API to UCI, XBoard, and homemade chess engines, using inherited Lichess API client code with additional PyChess/Fairy-Stockfish variant support.

Read `README.md` and `docs/pychess-quickstart.md` for PyChess setup and user-facing behavior. Consult the relevant page under `wiki/` for inherited engine features; its Lichess account and token instructions do not apply to PyChess. Inspect nearby code and tests before changing an established workflow.

## Repository Map

- `lichess-bot.py` is the CLI entry point; orchestration lives in `lib/lichess_bot.py`.
- `lib/` contains configuration, API, matchmaking, game models, engine wrappers, timers, and variant integration.
- `lib/variants.py` adapts python-chess interfaces to `pyffish` and `pyffish-alice`.
- `test_bot/` contains the pytest suite plus fake UCI/XBoard engines and API fixtures.
- `config.yml.default` documents the supported configuration surface. A local `config.yml` contains credentials and must remain untracked.
- `docker/` and `.github/workflows/` own container and CI behavior.
- `.github/workflows/pychess-bot-fork-ci.yml` is the fork's CI; `docs/upstream-workflows.md` explains ownership and publishing restrictions.

## Environment and Dependencies

Use uv for Python installation, dependency management, and command execution:

```bash
uv sync --locked
uv run --no-sync python lichess-bot.py --help
```

- Runtime and development dependencies live in `pyproject.toml`; exact resolutions live in `uv.lock`.
- Keep the existing `requirements.txt` and `test_bot/test-requirements.txt` consistent with `pyproject.toml` for upstream compatibility. Validate with `uv run python tools/check_dependency_sync.py`; do not introduce additional requirements files.
- Use uv in fork setup instructions and automation. Avoid rewriting inherited workflows solely to migrate their tooling.
- After changing dependencies, update the corresponding existing requirements file, run `uv lock`, then `uv sync --locked`, and commit the affected manifests and `uv.lock` together.
- Python 3.10 is the minimum runtime and Ruff language target. Check changed Python code with mypy at the Python 3.10 target, and use `typing_extensions` for typing features introduced after 3.10.

## Verification

Run commands through uv. Choose checks based on the files changed:

| Change scope | Required checks |
| --- | --- |
| Documentation or metadata only | Inspect the diff; validate any affected commands/configuration |
| Python code | `uv run ruff check --config test_bot/ruff.toml .`, `uv run mypy --strict --python-version 3.10 .`, and targeted pytest tests |
| Dependencies or shared infrastructure | The Python checks plus `uv run python tools/check_dependency_sync.py`, `uv lock --check`, and the deterministic suite below |
| Docker behavior | The Python checks plus a relevant Docker build or an explicit explanation if unavailable |

These lint/type commands assume a checkout without unrelated local Python files. If local artifacts interfere, pass explicit project source paths, including any new files, and report the scope checked. Do not modify unrelated files to make checks pass.

Mypy is the type checker installed by the development dependency group and used by fork CI. Pyright is an optional additional check, not a required clean baseline: existing code has diagnostics, especially for non-required TypedDict keys. If requested, compare its results with the pre-change baseline and report new diagnostics separately.

Target a test module or test first, for example:

```bash
uv run pytest test_bot/test_variants.py
uv run pytest test_bot/test_variants.py::test_name
```

Run the deterministic suite for broad changes:

```bash
uv run pytest --timeout=60 \
  --ignore=test_bot/test_bot.py \
  --ignore=test_bot/test_external_moves.py \
  --deselect=test_bot/test_lichess.py::test_lichess
```

`test_bot/test_bot.py` launches engine processes, while `test_bot/test_external_moves.py` downloads data or contacts external services. Run them when those integrations change and the needed environment is available. The deselected `test_lichess` case uses `LICHESS_BOT_TEST_TOKEN` and makes live requests; keep it excluded from offline runs even if that variable is set. Keep unit tests deterministic and mock network calls unless live integration is the purpose of the test.

The inherited engine simulator currently conflicts with the global `chess.Move` replacement in `lib/variants.py`, causing `FairyMove` constructor errors and timeouts. Distinguish reproduced baseline failures from regressions; report failures and unavailable checks explicitly.

## Upstream Syncs

- Prefer a normal merge from `upstream/master` to preserve both histories. Review incoming commits and the fork's differences before resolving conflicts.
- Preserve the variant adapter, Alice support, CECP notation handling, capability headers, challenge normalization, startup timeout, and fork-specific setup and CI behavior.
- Keep integration fixes focused and covered by relevant tests; avoid unrelated refactors during a sync.
- For a merge commit, compare against its first parent to review changes to the fork (`git diff HEAD^1 HEAD`), and against its second parent to inspect retained fork differences (`git diff HEAD^2 HEAD`). A combined merge diff may hide changes inherited from either parent.
- Keep upstream publishing guards intact. Do not enable inherited publishing jobs for the fork; follow `docs/upstream-workflows.md`.

## Change Guidelines

- Preserve public behavior inherited from lichess-bot unless the task explicitly changes it.
- Add or update tests alongside behavior changes, especially for challenge filtering, matchmaking, API payloads, engine protocols, and variant normalization.
- Treat Lichess event payloads as external input. The existing `total=False` TypedDicts model partially populated event variants; narrow by event type or check keys before introducing new access paths.
- Keep UCI/XBoard protocol output and engine lifecycle changes conservative. Tests use fake engines in `test_bot/` to cover these boundaries.
- Variant rules exist on both the python-chess-facing adapter and Fairy-Stockfish side. Verify FEN, UCI/SAN/XBoard notation, and legal-move behavior when touching `lib/variants.py` or engine wrappers.
- Never expose tokens or user configuration from `config.yml`, logs, engine files, or environment variables.
- Preserve unrelated working-tree changes and untracked local engine/configuration artifacts.

## Completion Checklist

- The implementation and tests match the requested behavior.
- Ruff passes with `test_bot/ruff.toml`, and strict mypy passes at the Python 3.10 target for project sources. Report any reproduced pre-existing failures separately.
- Relevant pytest tests pass; broad changes receive the deterministic suite and relevant integration tests when available.
- Dependency changes are reflected in consistent manifests and a checked lockfile.
- User-facing setup or configuration changes are documented.
