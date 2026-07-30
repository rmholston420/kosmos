# Tektos Plan Execution Smoke

Rename the function `greet_old` in `/workspace/src/hello.py` to `greet` while preserving its behavior. All callers currently use `greet_old` and must be updated to use `greet` as well.

The verifier will import `hello` and assert that `hello.greet("Kosmos") == "Hello, Kosmos!"` and that `greet_old` no longer exists.

Do not modify any file outside `/workspace/src/hello.py`.
