# Contributing to TigerDataLab

1. Fork and clone the repository.
2. Install in editable mode with dev dependencies:
   ```
   pip install -e ".[all,dev]"
   ```
3. Run the test suite before opening a PR:
   ```
   python -m pytest
   ```
4. Keep new analytics/chart/insight logic deterministic and rule-based by
   default — TigerDataLab's core must work without any LLM API key.
5. Add or update tests under `tests/` for any new module.
6. Follow the existing package layout (`io/`, `quality/`, `analytics/`,
   `insights/`, `visualization/`, `dashboard/`, `reporting/`, `dataops/`,
   `scale/`, `cli/`) rather than adding top-level modules.
