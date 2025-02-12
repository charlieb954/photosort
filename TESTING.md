# TESTING

To run the tests use `uv` to get the dependencies with:

```bash
uv venv
source .venv/bin/activate
uv sync
```

Then run the following commands to run the `pytest`s.

```bash
pytest --cov
```
