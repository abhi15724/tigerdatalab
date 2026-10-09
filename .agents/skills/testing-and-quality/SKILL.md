# Testing and Quality

1. Define acceptance criteria and regression risks before edits.
2. Add focused tests for the changed public behavior and negative/security cases.
3. Run the focused test file first, then relevant integration tests, then the full suite when practical.
4. Report exact commands and observed pass/fail results. A workflow being configured is not evidence that it passed.
5. Use fake providers and temporary directories for offline tests.
6. Test Python 3.10 compatibility and avoid introducing mandatory optional dependencies.
7. Do not skip important verification to save tokens; reduce unrelated context and scope instead.
