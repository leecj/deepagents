# Repository Guidelines

## Project Structure & Module Organization
- Core runtime lives in `src/deepagents/`; `graph.py`, `builder.py`, `sub_agent.py`, and `state.py` compose agent wiring, configuration, and state management.
- Shared prompt assets and typing helpers stay alongside the modules they support. Keep new primitives under `src/deepagents/` and expose them through `src/deepagents/__init__.py` when part of the public API.
- Example agents, configs, and logs live in `examples/`; the research workflow under `examples/research/` is the canonical integration reference.
- Distribution metadata (`pyproject.toml`, `deepagents.egg-info/`) drives packaging. Update these when you add new modules or dependencies.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — create an isolated environment before developing.
- `pip install -e .` — install the library locally with editable sources.
- `pip install -r examples/research/requirements.txt` — pull optional extras to exercise the research demo graph.
- `pytest -q` — run the test suite; use markers such as `pytest -q tests/test_builder.py::test_configurable_agent` when iterating on a single case.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indents and explicit type hints; mirror existing files that rely on `TypedDict` and `pydantic` models for schema validation.
- Use `snake_case` for functions and module-level variables, `PascalCase` for classes, and concise docstrings focused on agent behaviour or tool contracts.
- Prefer pure functions for prompt helpers and keep side effects (file IO, network calls) contained within tools; add brief comments only when logic is non-obvious.

## Testing Guidelines
- Author `pytest` tests under `tests/`, mirroring the package layout (`tests/test_graph.py`, etc.) so fixtures align with their targets.
- Cover both sync and async agent builders; mock external APIs (e.g., Tavily) and assert state transitions via `DeepAgentState` snapshots.
- Gate merges on a green local `pytest -q`; aim to add regression tests whenever you touch interrupt handling or tool scheduling paths.

## Commit & Pull Request Guidelines
- Keep commits small and descriptive; the history favours conventional prefixes such as `fix(...)` or `refactor(...)`. Reference the module or surface you touched.
- Every PR should include a summary, testing notes, and links to any related issues or discussions. Attach log snippets or screenshots when modifying agent workflows.
- Update documentation (`README.md`, `examples/`) alongside code changes, and flag any breaking API adjustments in the PR description.

## Agent & Prompt Tips
- When adding new sub-agents or tools, provide minimal runnable examples under `examples/` and document configuration hooks in the module docstring.
- Keep prompts versioned in-line with their consuming modules; note required env vars (`TAVILY_API_KEY`, etc.) in both code and docs to avoid runtime surprises.

## 语言
- 请使用中文和用户沟通，本项目文档、代码注释及提交信息均使用中文