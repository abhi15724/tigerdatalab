# TigerDataLab

**TigerDataLab is a production-ready, local-first data intelligence and AI application layer for companies.** It turns raw business data into trustworthy datasets, knowledge, workflows, tools and evaluation pipelines around the AI/LLM a company already uses.

> **Don’t replace your AI. Teach it your business.**

TigerDataLab complements existing models such as GPT, Claude, Gemini, Qwen, Llama and Mistral. It does not claim to retrain proprietary hosted models. Instead, it prepares high-quality training data, provides RAG, orchestrates supported fine-tuning, connects safe tools, runs business workflows and evaluates model behavior.

## v3.1.0 — Production AI Platform

The 3.1 release adds the missing application layer on top of the existing analytics and AI training-data foundation:

- AI provider abstraction with environment-based credentials
- Retrieval-augmented generation (RAG) knowledge base and deterministic lexical search
- Safe explicit tool registry and provider-compatible function schemas
- Deterministic business workflow engine with conditions and bounded execution
- Model router with ordered fallbacks
- Versioned registry for datasets, knowledge bases, models, tools, workflows, evaluations and systems
- `CompanyAI` composition API combining models, RAG, tools, workflows and evaluation
- Existing analytics, DataOps, large-data, dashboard, reporting and training-data APIs preserved
- Optional Hugging Face + TRL fine-tuning remains opt-in
- Core runtime remains free of mandatory LLM vendor SDKs
- Python 3.10–3.13 supported
- GitHub Actions + PyPI Trusted Publishing release pipeline

## What TigerDataLab does

```text
Company data
    ↓
Clean + validate + protect PII
    ↓
Training datasets / knowledge base
    ↓
RAG + fine-tuning + tools
    ↓
Existing AI/LLM
    ↓
Business workflow
    ↓
Evaluation
    ↓
Company-specific AI application
```

### Example business workflow

A logistics company can implement:

```text
Customer asks about shipment
        ↓
Retrieve company policy + shipment context
        ↓
Check shipment status
        ↓
Calculate SLA breach
        ↓
Determine compensation eligibility
        ↓
Generate customer response
        ↓
Escalate if required
```

## Install

```bash
python -m pip install tigerdatalab
```

Optional large-data/reporting dependencies:

```bash
python -m pip install "tigerdatalab[all]"
```

Optional model-training backend:

```bash
python -m pip install "tigerdatalab[train]"
```

## Quick start: data → AI training set

```python
from tigerdatalab.ai import AIDataset

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

data = AIDataset(rows, task="sft").run()
print(data.stats)
data.export("training_data")
```

The pipeline supports format conversion, schema validation, quality scoring, PII detection/masking, deduplication, deterministic splitting, lineage and JSONL export.

## Build a company AI application

```python
from tigerdatalab.ai import CompanyAI, KnowledgeBase, ModelRouter, OpenAIProvider

provider = OpenAIProvider()  # reads OPENAI_API_KEY from the environment
router = ModelRouter().add(provider, "your-model")

kb = KnowledgeBase()
kb.add("returns", "Customers can return unused products within 30 days.")

ai = CompanyAI(router, knowledge_base=kb)
result = ai.ask("What is the return policy?")
print(result.output)
```

No API key is stored in datasets, lineage or registry metadata.

## RAG / knowledge base

```python
from tigerdatalab.ai import KnowledgeBase

kb = KnowledgeBase()
kb.add("policy", "Refunds are issued within 7 business days.", department="finance")
kb.add("support", "Priority customers receive 24/7 support.", department="support")

print(kb.search("refund timing", top_k=3))
print(kb.context("refund timing"))
```

TigerDataLab's core RAG implementation is intentionally dependency-light. Production deployments can place an embedding/vector database behind the same application boundary without forcing that infrastructure on every user.

## Safe tools / function calling

```python
from tigerdatalab.ai import Tool, ToolRegistry

registry = ToolRegistry()
registry.register(Tool(
    name="get_order",
    description="Get an order by ID",
    function=lambda order_id: {"id": order_id, "status": "shipped"},
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
))

print(registry.schemas())
print(registry.execute("get_order", {"order_id": "ORD-1001"}))
```

Only explicitly registered tools can execute. Model output is never treated as arbitrary Python or shell code.

## Business workflows

```python
from tigerdatalab.ai import Workflow, WorkflowStep

workflow = Workflow("order-support")
workflow.add_step(WorkflowStep("load", lambda s: {"order": {"status": "delayed"}}))
workflow.add_step(WorkflowStep("decision", lambda s: "escalate" if s["order"]["status"] == "delayed" else "resolve", output_key="decision"))

result = workflow.run({"order_id": "ORD-1001"})
print(result.status, result.state)
```

Workflows support ordered steps, conditions, output keys, validation and bounded execution.

## Model routing

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider

router = ModelRouter()
router.add(OpenAIProvider(), "primary-model")
router.add(OpenAIProvider(), "fallback-model")

response = router.chat([{"role": "user", "content": "Summarize this order."}])
```

The router tries configured targets in order and falls back when a target fails. Provider credentials remain outside application data.

## Evaluation

```python
from tigerdatalab.ai import evaluate

records = [
    {"prompt": "2+2?", "expected": "4"},
]

result = evaluate(lambda messages: "4", records)
print(result.score, result.average_latency_ms)
```

Evaluation provides pass/fail counts, score, latency and failure details. For production systems, use task-specific scorers and representative test sets rather than relying only on exact-match evaluation.

## Fine-tuning

```python
from tigerdatalab.ai import LLMTrainer

trainer = LLMTrainer("Qwen/Qwen3-0.6B", "./model")
trainer.train_sft("training_data/train.jsonl", epochs=1)
```

Install `tigerdatalab[train]` only when needed. Actual training is performed by PyTorch, Transformers, Hugging Face Datasets and TRL. TigerDataLab orchestrates the data and training workflow.

## Analytics platform

TigerDataLab continues to provide its existing data analytics capabilities:

```python
import tigerdatalab as tdl

result = tdl.analyze("sales.xlsx")
print(result.summary())
print(result.kpis())
print(result.quality())
print(result.insights())
result.dashboard("analysis/dashboard.html")
result.report("analysis")
```

Large data:

```python
data = tdl.large("large_sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
```

DataOps remains available for controlled, audited data changes.

## Architecture

```text
                    TigerDataLab
┌──────────────────────────────────────────────────────┐
│ Analytics │ Data Quality │ DataOps │ Dashboards      │
├──────────────────────────────────────────────────────┤
│ Training Data │ PII │ Lineage │ Fine-tuning         │
├──────────────────────────────────────────────────────┤
│ RAG │ Providers │ Tools │ Workflows │ Router        │
├──────────────────────────────────────────────────────┤
│ Registry │ Evaluation │ CompanyAI                    │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
                 Existing AI / LLM
                         │
                         ▼
                  Company workflow
```

## Public AI API

```python
from tigerdatalab.ai import (
    AIDataset, CompanyAI, KnowledgeBase, ModelRouter, OpenAIProvider,
    Tool, ToolRegistry, Workflow, WorkflowStep, Registry, Asset,
    Evaluator, evaluate, LLMTrainer, train_sft,
)
```

## Security principles

- Local-first data processing by default.
- No mandatory LLM API for dataset preparation.
- API credentials are read from environment variables.
- PII scanning/masking happens locally in the training-data pipeline.
- Tool execution is explicit and allow-listed.
- Workflow execution is bounded and deterministic.
- Training data and model outputs should be reviewed before production use.
- TigerDataLab does not imply that a hosted proprietary model can be fine-tuned through its API unless that provider explicitly supports it.

## Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

Build validation:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## Release

The repository uses GitHub Actions and PyPI Trusted Publishing/OIDC. A **published GitHub Release** triggers tests, package build, metadata validation and PyPI publishing.

For v3.1.0:

```text
main → CI → GitHub Release v3.1.0 → publish workflow → PyPI
```

## Project layout

```text
tigerdatalab/
├── analytics/ quality/ insights/ visualization/
├── dashboard/ reporting/ dataops/ scale/
├── ai/
│   ├── datasets.py
│   ├── pipeline.py
│   ├── privacy.py
│   ├── quality.py
│   ├── schema.py
│   ├── training.py
│   ├── providers.py
│   ├── rag.py
│   ├── evaluation.py
│   ├── tools.py
│   ├── workflows.py
│   ├── router.py
│   ├── registry.py
│   └── system.py
└── cli/
```

## License

MIT License.
