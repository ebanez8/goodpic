# Testing strategy

The scaffold is checked by importing modules, parsing the JSON fixture, validating `pyproject.toml`, and running `ruff`/`mypy` when installed. Future unit tests should target coordinate and wire-format invariants; integration tests should use disposable archive copies. Never mutate `t/` or known-good templates. A Goodnotes application import/reopen and partial-erase check is a manual acceptance test. Record the app version and screenshots or PDF exports with experiment records.
