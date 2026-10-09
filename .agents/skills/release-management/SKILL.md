# Release Management

- Inspect the default branch, current release version, existing PRs and CI status before publishing changes.
- Work on a feature branch; do not force-push, rewrite history, or merge to main unless explicitly asked.
- Keep PRs focused, with summary, compatibility notes, test commands and known limitations.
- Check CI results after the PR is opened. If CI fails, inspect logs and fix the root cause before describing the work as complete.
- Update README/API docs only after confirming the API exists.
- Do not bump package versions merely for internal scaffolding; coordinate versioning with a release plan.
