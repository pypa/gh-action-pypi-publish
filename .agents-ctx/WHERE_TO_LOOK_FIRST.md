# Where to Look First

When picking up a task, get oriented before proposing anything.
Read, in this order:

1. The packaging metadata -- what the project is, what it depends
   on, what it exposes.
2. The source of the module the task is about.
3. The shared test fixtures, then the tests for that module --
   they are the behavioral contract.
4. `tox.ini` and `.pre-commit-config.yaml` -- how things get run
   locally and in CI.
5. The main CI/CD workflow.

Here:

1. `action.yml` -- the composite action's inputs and steps. There
   is no packaging metadata.
2. `create-docker-action.py`, which generates the Docker-based
   action the composite one runs, then the scripts run inside the
   container: `twine-upload.sh`, `oidc-exchange.py`,
   `attestations.py`, `print-hash.py`, `print-pkg-names.py`.
3. There's no unit test suite; read
   `.github/workflows/reusable-smoke-test.yml`, which publishes to
   a throwaway devpi server.
4. `.pre-commit-config.yaml` -- there's no `tox.ini`.
5. `.github/workflows/`, including the Docker image build.

Other places worth knowing:

- `Dockerfile` and `requirements/` -- the container image and its
  pinned runtime dependencies, compiled with pip-tools
  (`.pip-tools.toml`).
- `_type_stubs/` -- type stubs for untyped dependencies.
- `README.md` -- the user-facing documentation.
