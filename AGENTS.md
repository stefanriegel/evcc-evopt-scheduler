# Agent Guidelines for `evcc-evopt-scheduler`

1. This repository focuses on a Home Assistant add-on located under `evcc-evopt-scheduler/`.
2. Build, lint, and test commands are executed inside the container image:
   - Build: `docker build -t evcc-evopt-scheduler evcc-evopt-scheduler`
   - Lint: `python -m py_compile evcc-evopt-scheduler/app/main.py`
   - Run single test (if present): `pytest evcc-evopt-scheduler/tests::TestClass::test_case`
3. Python formatting follows Black defaults (4-space indent, 88 char line length).
4. Use absolute imports within `app/` modules; avoid relative imports that cross package boundaries.
5. Prefer dataclasses for structured configuration/state objects.
6. All HTTP I/O must use `aiohttp` with explicit timeouts and logging on failure.
7. Keep the REST API surface documented in `evcc-evopt-scheduler/README.md` in sync with the implementation.
8. Optimization payloads must remain compatible with EVOpt's swagger definition (`dt`, `gt`, `ft`, `p_N`, `p_E`).
9. Update `/share/evcc-evopt-scheduler/last_request.json` and `last_response.json` whenever an optimization runs.
10. When modifying config schema, adjust both `config.yaml` and Python parsing logic.
11. Battery limits should never exceed configured max/min SoC.
12. Use `ZoneInfo` for all timezone conversions; default to `Europe/Berlin` on failure.
13. REST handlers must return JSON responses with proper status codes.
14. Long-running loops should catch exceptions and log warnings rather than crash the supervisor.
15. When persisting files, ensure `SHARE_DIR` exists and handle write errors gracefully.
16. Do not reintroduce the legacy `custom_components/evopt` integration unless explicitly requested.
17. Keep the root `README.md` aligned with the add-on's purpose and structure.
18. Prefer type hints and `# type: ignore` comments when stubs are unavailable.
19. Tests (if added) belong under `evcc-evopt-scheduler/tests` using pytest.
20. Log levels should be configurable via the add-on options; default to `INFO`.
21. The REST API port is configurable (`api_port` in `config.yaml`); keep documentation in sync with defaults.
