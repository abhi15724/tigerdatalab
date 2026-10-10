# TigerDataLab Vercel Staging

This folder is a separate Vercel project root for testing the **published PyPI
release** of TigerDataLab, rather than importing the repository checkout.

## Runtime compatibility

- Python is pinned to 3.12 via `requires-python = "~=3.12.0"`.
- Installs `tigerdatalab[deployment]==4.1.1` from PyPI.
- Uses the framework's existing FastAPI deployment interface and Groq adapter.
- Exposes `GET /health`, `GET /ready`, and authenticated `POST /v1/ask`.
- Uses `openai/gpt-oss-20b` as the initial model default; override it using
  `GROQ_MODEL` only after confirming the model is available in the Groq project.
- The provider timeout defaults to 35 seconds and can be set with
  `GROQ_TIMEOUT_SECONDS` (1–120 seconds).

Vercel supports FastAPI backends, but deployment success, dependency bundle
size, function duration, and live provider inference must be verified in the
target Vercel account. This configuration is a staging starting point, not a
production certification.

## Deploy

1. In Vercel, create a new project and import
   `https://github.com/abhi15724/tigerdatalab`.
2. Set **Root Directory** to `deploy/vercel-staging`.
3. Before relying on the deployment, add the following Environment Variables
   for the **Preview** environment (and only add to Production if intentionally
   promoting later):
   - `GROQ_API_KEY`: secret generated in the Groq console.
   - `TIGERDATALAB_API_KEY`: a long, random, dedicated staging API credential.
   - `GROQ_MODEL`: optional; defaults to `openai/gpt-oss-20b`.
   - `GROQ_TIMEOUT_SECONDS`: optional; defaults to `35`.
4. Deploy and check `https://YOUR-VERCEL-DOMAIN/health` and
   `/ready`. These endpoints should return HTTP 200.
5. Verify `POST /v1/ask` rejects missing and invalid bearer credentials with
   HTTP 401. With the staging API key, send JSON:
   `{"prompt":"Reply with exactly: TIGERDATALAB_STAGING_OK"}`
6. In the GitHub repository, open Settings → Environments → staging. Add the
   environment variable `TIGERDATALAB_STAGING_URL` (the HTTPS base URL) and
   secret `TIGERDATALAB_STAGING_API_KEY` (same value as the Vercel
   `TIGERDATALAB_API_KEY`). Do not put either secret in source control or chat.
7. Run Actions → Staging verification → Run workflow. First leave
   `exercise_model` disabled to verify health and authentication. Then run it
   enabled to perform one real inference request, which may incur Groq usage.

## Important limitations

- The default in-memory rate limit and audit log are process-local and are not
  distributed controls. Do not treat them as global rate limiting or durable
  audit storage in a serverless deployment.
- This staging entrypoint creates one agent at module initialization. Do not
  use process memory for durable conversation state or cross-request workflow
  coordination.
- The app uses the published PyPI version 4.1.1. Changes made only on GitHub
  are not present until a new version is published and this dependency pin is
  deliberately updated.
- Test concurrency, timeouts, model errors, costs, secrets, dependency build
  size, backup/restore, and rollback before any workload-specific production
  decision.
