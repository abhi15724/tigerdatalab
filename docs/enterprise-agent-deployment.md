# TigerDataLab Enterprise Agent Deployment

TigerDataLab can expose a ready CompanyAgent as a real-time HTTP service. The deployment layer provides health/readiness endpoints, API-key authentication, in-process rate limiting and an audit hook.

## Build the agent

```python
import tigerdatalab as td
from tigerdatalab.ai.providers import OpenRouterProvider

project = td.create_project("Acme")
agent = project.company_agent("ap-agent")

agent.add_knowledge(
    "ap-policy",
    "Invoices above INR 100000 require two approvals.",
    department="finance",
)

agent.connect(
    OpenRouterProvider(),
    model="YOUR_MODEL",
    system="You are the Acme AP assistant. Follow company policy.",
)
```

## Secure local/container deployment

Set a secret outside source control:

```bash
export TIGERDATALAB_API_KEY="replace-with-a-long-random-secret"
pip install "tigerdatalab[deployment]"
```

Then:

```python
agent.deploy(
    host="0.0.0.0",
    port=8000,
    api_key=None,  # reads TIGERDATALAB_API_KEY
    rate_limit=60,
    rate_window_seconds=60,
)
```

`0.0.0.0` listens on all interfaces. It does **not** itself create a public internet endpoint. Put an HTTPS reverse proxy/API gateway in front of an internet-facing deployment.

## API

Health:

```http
GET /health
```

Readiness:

```http
GET /ready
```

Inference:

```http
POST /v1/ask
Authorization: Bearer <API_KEY>
Content-Type: application/json

{"prompt":"What is the AP approval policy?"}
```

Workflow execution:

```http
POST /v1/run
Authorization: Bearer <API_KEY>
Content-Type: application/json

{"invoice_id":"INV-1023"}
```

Audit inspection for the built-in in-memory sink:

```http
GET /v1/audit
Authorization: Bearer <API_KEY>
```

## Production architecture

```text
Employee / Company App
          |
       HTTPS
          |
 API Gateway / Reverse Proxy
          |
 Authentication + WAF + rate limits
          |
 TigerDataLab Agent Runtime
          |
   +------+-------+
   |              |
Knowledge       Tools
   |              |
   +------+-------+
          |
      ModelRouter
          |
 OpenRouter / OpenAI / other provider
          |
 Company systems (approved APIs/DBs)
```

## Security model

- Keep model, ERP, database and API credentials in a secret manager/environment variables.
- Use explicit allow-listed tools rather than unrestricted model access.
- Use the existing TigerDataLab permission layer for tool authorization.
- Require human approval for sensitive business actions.
- Use HTTPS/TLS at the gateway or Uvicorn where appropriate.
- Use a durable external audit sink for enterprise retention; the built-in audit log is process-local.
- Use an external distributed rate limiter when running multiple replicas.
- Put the service behind a corporate identity/API gateway for SSO, RBAC and network policy.

## Docker

The repository includes a baseline `Dockerfile`. Supply your own agent factory with:

```bash
TIGER_AGENT_FACTORY=my_app:build_agent
TIGERDATALAB_API_KEY=replace-with-a-long-random-secret
```

The factory must return a ready `CompanyAgent`. This keeps customer-specific application code and credentials outside the TigerDataLab package image.

## Important boundary

TigerDataLab provides the agent SDK/runtime and security primitives. Enterprise infrastructure such as a cloud load balancer, WAF, centralized identity, secret manager, durable audit/SIEM, distributed rate limiter, private networking and autoscaling should be supplied by the customer's production environment.
