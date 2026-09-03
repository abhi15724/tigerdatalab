# Deploy a TigerDataLab Company AI Agent

After building and evaluating a company agent, TigerDataLab can expose it as a real-time HTTP service.

## Install

```bash
pip install "tigerdatalab[deployment]"
```

## Run locally

```python
import tigerdatalab as td
from tigerdatalab.ai.providers import OpenRouterProvider

project = td.create_project("Acme")
agent = project.company_agent("support-agent")

agent.add_knowledge(
    "returns-policy",
    "Unused products may be returned within 30 days.",
    department="support",
)

agent.connect(
    OpenRouterProvider(),
    model="YOUR_OPENROUTER_MODEL",
    system="You are Acme Support. Follow company policy and do not invent policies.",
)

agent.deploy(host="0.0.0.0", port=8000)
```

The service exposes:

- `GET /health` — process health
- `GET /ready` — readiness check
- `POST /v1/ask` — real-time agent inference
- `POST /v1/run` — execute the configured business workflow

Example request:

```bash
curl -X POST http://localhost:8000/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is the return policy?"}'
```

## Cloud/container deployment

For production, use the ASGI application instead of starting the development server from application code:

```python
app = agent.app()
```

Then run it with your chosen process/container platform, for example:

```bash
uvicorn my_service:app --host 0.0.0.0 --port 8000
```

The deployment layer intentionally does not provide authentication, TLS termination, persistent queues, autoscaling or secrets management. For enterprise production, put the service behind an API gateway/load balancer, TLS, authentication/authorization, rate limits, observability, secret management and a process/container orchestrator appropriate to the customer's environment.

## Production lifecycle

```text
Company data / SOPs
       ↓
TigerDataLab data preparation
       ↓
Knowledge + optional fine-tuning
       ↓
Tools + controlled workflows
       ↓
Evaluation / approval
       ↓
agent.app()
       ↓
Container / ASGI server / cloud platform
       ↓
Real-time company AI API
```

Deployment is the final runtime stage; it does not automatically make an unvalidated agent safe for autonomous business actions. Keep high-impact actions allow-listed and require human approval where appropriate.
