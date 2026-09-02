# TigerDataLab

**TigerDataLab is a unified, local-first Data + AI engineering platform for Data Analytics, Data Science, Data Engineering, AI Training, and Company AI.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

TigerDataLab connects the full lifecycle from raw business data to trusted analytics, machine-learning datasets, AI training datasets, RAG knowledge, business workflows, tools, evaluation, and production AI applications.

## v4.0.0 — Unified Data-to-AI Platform

TigerDataLab now provides one project-level API across five disciplines:

| Area | What TigerDataLab provides |
|---|---|
| **Data Analytics** | Profiling, quality checks, KPIs, insights, trends, dashboards and reports |
| **Data Science** | Reproducible splits, statistical exploration, correlations and ML-ready datasets |
| **Data Engineering** | Local ETL pipelines, transformations, data loading, manifests and large-data integrations |
| **AI Training** | SFT, DPO, classification/text datasets, PII protection, deduplication, validation, lineage and compatible model training |
| **Company AI** | RAG, company knowledge, business rules, workflows, tools/APIs, model routing and evaluation |

Existing APIs remain available for backward compatibility.

## The complete lifecycle

```text
                         COMPANY DATA
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          CSV/Excel        Databases        APIs/Files
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    TIGERDATALAB DATA LAYER
                              │
                Clean • Validate • Profile • PII
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
          Analytics      Data Science   Data Engineering
               │              │              │
               └──────────────┼──────────────┘
                              ▼
                       TRUSTED DATA
                              │
                         AI DATA LAYER
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
          GENERAL AI TRAINING          COMPANY AI
                │                           │
          SFT / DPO / Classify        RAG / Rules
          Fine-tuning / Text          Workflows / Tools
                │                           │
                └─────────────┬─────────────┘
                              ▼
                         AI / LLM LAYER
                              │
             OpenAI • Claude • Gemini • Groq
          Mistral • OpenRouter • Qwen • Llama • Local
                              │
                              ▼
                   EVALUATION + MONITORING
                              │
                              ▼
                     PRODUCTION AI SYSTEM
```

## Installation

```bash
python -m pip install tigerdatalab
```

For compatible open/self-hosted model training:

```bash
python -m pip install "tigerdatalab[train]"
```

For large-data and PDF capabilities:

```bash
python -m pip install "tigerdatalab[all]"
```

## Unified platform API

```python
from tigerdatalab import create_project

tdl = create_project("my-company")
```

### Data Analytics

```python
result = tdl.analyze("sales.xlsx")
print(result.summary())
print(result.kpis())
print(result.quality())
print(result.insights())
```

The original analytics API remains available:

```python
import tigerdatalab as tdl
result = tdl.analyze("sales.xlsx")
```

### Data Engineering

Build deterministic, testable transformations without creating a heavyweight orchestration dependency:

```python
frame = tdl.load("sales.csv")

pipeline = (
    tdl.engineering
    .add("fill_missing", lambda df: df.fillna(0))
    .add("positive_sales", lambda df: df[df["sales"] >= 0])
)

clean = pipeline.run(frame)
pipeline.save_manifest("pipeline.json")
```

The pipeline validates that every transformation returns a DataFrame and records the ordered step names in its manifest.

### Data Science

```python
profile = tdl.profile(frame)
print(profile.rows, profile.columns)
print(profile.numeric_columns)

train, test = tdl.data_science.train_test_split(frame, test_size=0.2, seed=42)
correlation = tdl.data_science.correlation(train)
```

Splits are reproducible through an explicit seed.

## AI Training

Create a general AI training project:

```python
ai_project = tdl.ai_training("support-model", task="sft")

dataset = ai_project.prepare("support_examples.csv", "training_data")
print(dataset.summary())
```

TigerDataLab's AI data layer performs:

- input ingestion
- task formatting
- schema validation
- quality checks
- PII detection and masking
- deduplication
- deterministic train/validation/test splitting
- dataset lineage
- dataset cards and quality reports
- standard JSONL export

### Train a compatible open/self-hosted model

```python
trainer = ai_project.trainer("Qwen/Qwen3-0.6B", "./models/support")
trainer.train_sft("training_data/train.jsonl", epochs=1)
```

The built-in training backend uses compatible Transformers/TRL/PyTorch stacks.

### Universal training architecture

TigerDataLab does not falsely claim that every proprietary hosted model can be fine-tuned. Instead, it provides an adapter contract:

```text
TigerDataLab Universal Training API
              │
     ┌────────┼──────────┐
     ▼        ▼          ▼
Transformers Vendor API Custom Backend
     │        │          │
Open models  Supported   Internal/vendor
             hosted      training system
             tuning
```

For custom training systems, implement `TrainingBackend` or use `CallableTrainingBackend`.

## Company AI

Company AI combines **knowledge + behavior + workflow + tools**.

```python
from tigerdatalab.ai import OpenAIProvider

company = tdl.company_ai("customer-support")
company.add_knowledge(
    "returns-policy",
    "Unused products can be returned within 30 days.",
    department="support",
)
company.connect(OpenAIProvider(), "your-model", system="Follow company policy.")

answer = company.ask("Can this customer return the product?")
print(answer.output)
```

The API key is read from the provider environment configuration and is not placed into datasets or lineage metadata.

### Company workflow

Company AI can be composed with TigerDataLab workflows:

```text
Customer request
      ↓
Identify intent
      ↓
Retrieve company knowledge
      ↓
Check business rules
      ↓
Call approved tools/APIs
      ↓
Make decision
      ↓
Generate response
      ↓
Escalate when required
```

This is different from simply fine-tuning an LLM. Fine-tuning can teach stable behavior and output patterns; RAG supplies changing knowledge; workflows and tools enforce the actual business process.

## AI provider layer

TigerDataLab supports provider adapters for model APIs including:

- OpenAI
- Anthropic
- Google Gemini
- Groq
- OpenRouter
- Mistral
- Together AI
- OpenAI-compatible endpoints

Example:

```python
from tigerdatalab.ai import get_provider

provider = get_provider("openai")
```

Provider credentials should be supplied through environment variables or an external secrets manager in production. Never commit API keys to source control.

## RAG / company knowledge

```python
from tigerdatalab.ai import KnowledgeBase

kb = KnowledgeBase()
kb.add("finance", "Refunds are issued within 7 business days.")
kb.add("support", "Priority customers receive 24/7 support.")

print(kb.search("refund timing", top_k=3))
```

The built-in implementation is dependency-light and deterministic. Production deployments can place an embedding model and vector database behind the same knowledge boundary.

## Safe tools

TigerDataLab uses explicit tool registration. Model output is not executed as arbitrary Python or shell code.

```python
from tigerdatalab.ai import Tool, ToolRegistry

registry = ToolRegistry()
registry.register(Tool(
    name="get_order",
    description="Get an order by ID",
    function=get_order,
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
))
```

## Evaluation

Every production AI application should be evaluated against representative test cases:

```python
from tigerdatalab.ai import evaluate

result = evaluate(
    lambda messages: "4",
    [{"prompt": "2+2?", "expected": "4"}],
)

print(result.score)
print(result.average_latency_ms)
```

Use task-specific scorers and regression datasets for real deployments.

## Model routing

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider

router = ModelRouter()
router.add(OpenAIProvider(), "primary-model")
router.add(OpenAIProvider(), "fallback-model")
```

The router can provide ordered fallback between configured targets.

## Production architecture

```text
┌────────────────────────────────────────────────────────────┐
│                    TIGERDATALAB 4.0                        │
├────────────────────────────────────────────────────────────┤
│ Data Analytics │ Data Science │ Data Engineering          │
├────────────────────────────────────────────────────────────┤
│ Data Quality │ PII │ Lineage │ Governance │ DataOps        │
├────────────────────────────────────────────────────────────┤
│ AI Dataset │ Universal Training │ Model Registry            │
├────────────────────────────────────────────────────────────┤
│ RAG │ Providers │ Tools │ Workflows │ Router │ Company AI  │
├────────────────────────────────────────────────────────────┤
│ Evaluation │ Testing │ Monitoring │ Deployment             │
└────────────────────────────────────────────────────────────┘
                         │
                         ▼
                Supported AI systems
                         │
                         ▼
                  Company AI / ML
```

## Production principles

TigerDataLab is designed around these principles:

- **Local-first:** data preparation does not require an LLM API.
- **Model-agnostic:** providers and training systems are adapter-based.
- **Backward compatible:** existing analytics and AI APIs remain available.
- **Reproducible:** deterministic dataset splitting and data-science seeds are supported.
- **Secure by design:** credentials stay outside datasets and lineage; tools are allow-listed.
- **Observable:** evaluation, lineage, manifests and quality reports provide inspectable evidence.
- **Explicit capabilities:** unsupported training operations fail clearly instead of pretending every model is trainable.
- **Human review:** production decisions should use approval gates where business risk requires them.

## What TigerDataLab is — and is not

### TigerDataLab is

A **Data-to-AI engineering platform** that helps teams turn raw data and business processes into trustworthy analytics, training datasets, knowledge systems, workflows and AI applications.

### TigerDataLab is not

A claim that one API can modify the weights of every proprietary LLM. Hosted models can only be fine-tuned when their provider exposes a compatible training capability. Unsupported models can still be improved at the application layer through RAG, tools, workflows, routing and evaluation.

## Project layout

```text
tigerdatalab/
├── analytics/          # Business analytics
├── dashboard/          # Dashboard generation
├── dataops/             # Data operations
├── insights/            # Insight generation
├── ai/                  # Training, RAG, providers, tools, workflows
├── cli/                 # Command-line interface
├── core.py              # Core analytics API
├── platform.py          # Unified Data-to-AI project API
└── config.py            # Package configuration
```

## Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

CLI smoke test:

```bash
tigerdatalab analyze tests/data/sales.csv
```

## Version

**4.0.0** — Unified Data-to-AI Platform.

## License

MIT License.
