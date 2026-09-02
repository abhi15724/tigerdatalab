# TigerDataLab

**TigerDataLab is a unified, local-first Data + AI engineering platform for Data Analytics, Data Science, Data Engineering, AI Training, and Company AI workflow training.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

TigerDataLab connects the lifecycle from raw business data to trusted analytics, machine-learning datasets, AI training datasets, company knowledge, RAG, business workflows, approved tools, evaluation, and production AI applications.

## v4.0.0 — Unified Data-to-AI Platform

One project-level API covers five practical roles:

| Role | How TigerDataLab helps |
|---|---|
| **Data Analyst** | Profile data, check quality, calculate KPIs, discover insights/trends, generate dashboards and reports |
| **Data Scientist** | Explore datasets, create reproducible train/test splits, analyze correlations and prepare ML-ready data |
| **Data Engineer** | Build deterministic ETL pipelines, load data, transform datasets and save pipeline manifests |
| **AI Engineer / ML Engineer** | Build training datasets, mask PII, deduplicate, validate, split, export and train compatible models |
| **Company AI Builder** | Combine company knowledge, RAG, business rules, workflows, approved tools/APIs, model routing and evaluation |

Existing APIs remain available for backward compatibility.

## What can you build with TigerDataLab?

```text
Raw Company Data
      ↓
Data Engineering
      ↓
Data Quality + PII Protection
      ↓
Data Analytics / Data Science
      ↓
Trusted Data
      ↓
AI Dataset Builder
      ↓
 ┌───────────────────────┬────────────────────────┐
 │ General AI Training   │ Company AI              │
 │ SFT / DPO / Text      │ RAG / Rules / Workflow │
 │ Classification        │ Tools / APIs           │
 └───────────────────────┴────────────────────────┘
      ↓
Compatible AI / LLM
      ↓
Evaluation
      ↓
Production AI System
```

---

# Installation

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

---

# Quick Start

```python
from tigerdatalab import create_project

tdl = create_project("my-company")
```

The same project can be used for analytics, engineering, data science, AI training and company AI.

---

# 1. Data Analyst — Analyze Business Data

Use TigerDataLab when you receive a CSV, Excel, JSON, Parquet or other supported business dataset and need to understand what is happening in the business.

### Typical workflow

```text
Sales / Finance / Customer Data
            ↓
       Load Dataset
            ↓
    Profile + Quality Check
            ↓
       KPIs + Trends
            ↓
       Business Insights
            ↓
      Dashboard / Report
```

### Example

```python
from tigerdatalab import create_project

tdl = create_project("sales-analysis")

result = tdl.analyze("sales.xlsx")

print(result.summary())
print(result.kpis())
print(result.quality())
print(result.insights())
```

You can use the original API too:

```python
import tigerdatalab as tdl

result = tdl.analyze("sales.xlsx")
```

### Data Analyst use cases

- Sales and revenue analysis
- Customer analysis
- Finance reporting
- KPI monitoring
- Data-quality investigation
- Trend analysis
- Business insights
- Dashboard generation
- PDF/report generation

---

# 2. Data Scientist — Prepare and Explore ML Data

TigerDataLab can be used before model development to understand data and create reproducible datasets.

### Example

```python
frame = tdl.load("customers.csv")

profile = tdl.profile(frame)

print("Rows:", profile.rows)
print("Columns:", profile.columns)
print("Numeric:", profile.numeric_columns)
print("Categorical:", profile.categorical_columns)

train, test = tdl.data_science.train_test_split(
    frame,
    test_size=0.2,
    seed=42,
)

correlation = tdl.data_science.correlation(train)
print(correlation)
```

### Data Scientist workflow

```text
Raw Dataset
    ↓
Profile
    ↓
Quality Check
    ↓
Clean / Transform
    ↓
Train / Test Split
    ↓
Feature / Statistical Analysis
    ↓
ML Training
```

The explicit seed makes the split reproducible.

TigerDataLab is focused on the data engineering and data preparation layer; you can connect the resulting data to your preferred ML framework.

---

# 3. Data Engineer — Build ETL Pipelines

Use the engineering API to create deterministic, testable transformations.

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

Every transformation must return a pandas DataFrame. The manifest records the ordered pipeline steps, making the transformation process inspectable and easier to test in CI/CD.

### Data Engineering workflow

```text
CSV / Excel / JSON / Parquet / Database
                  ↓
                Load
                  ↓
              Validate
                  ↓
          Transform / Clean
                  ↓
             Aggregate
                  ↓
             Trusted Data
                  ↓
       Analytics / ML / AI Layer
```

### Data Engineering use cases

- ETL/ELT preparation
- Data cleaning
- Schema-aware transformations
- Reproducible pipelines
- Data quality workflows
- Data preparation for ML/AI
- Large-data processing integrations

---

# 4. AI Training — Build High-Quality Training Data

TigerDataLab provides the **AI data and training layer** between raw data and a compatible training system.

### AI training workflow

```text
Raw Examples / Company Records
              ↓
            Ingest
              ↓
        Task Formatting
              ↓
        PII Detection/Mask
              ↓
          Deduplication
              ↓
        Schema Validation
              ↓
          Quality Check
              ↓
     Train / Validation / Test
              ↓
          JSONL Export
              ↓
     Compatible Training Backend
```

### Create a training project

```python
ai_project = tdl.ai_training(
    "support-model",
    task="sft",
)

dataset = ai_project.prepare(
    "support_examples.csv",
    "training_data",
)

print(dataset.summary())
```

### Supported dataset styles

TigerDataLab's training data layer supports common formats such as:

- **SFT** — supervised instruction/chat examples
- **DPO** — prompt + preferred/rejected responses
- **Classification** — text + label
- **Instruction** — instruction/input/output
- **Text** — general text training data

### Dataset quality features

The preparation pipeline can provide:

- Input ingestion
- Task formatting
- Schema validation
- Quality checks
- PII detection and masking
- Deduplication
- Deterministic train/validation/test splitting
- Dataset lineage
- Dataset cards
- Quality reports
- Standard JSONL export

### Train a compatible open/self-hosted model

```python
trainer = ai_project.trainer(
    "Qwen/Qwen3-0.6B",
    "./models/support",
)

trainer.train_sft(
    "training_data/train.jsonl",
    epochs=1,
)
```

The built-in backend uses compatible Transformers/TRL/PyTorch training stacks.

### Universal training architecture

TigerDataLab is model-agnostic through adapters, but it does **not** falsely claim that every proprietary hosted model can have its weights modified.

```text
                 TigerDataLab
              Universal Training
                      ↓
        ┌─────────────┼──────────────┐
        ↓             ↓              ↓
 Transformers     Provider API    Custom Backend
        ↓             ↓              ↓
 Open models    Supported hosted   Enterprise /
                fine-tuning        private system
```

Implement `TrainingBackend` or use `CallableTrainingBackend` when your organization has its own training infrastructure.

---

# 5. Company AI — Train the AI to Follow Your Business

Company AI is different from simply fine-tuning an LLM.

A company AI system usually needs four layers:

```text
1. KNOWLEDGE   → What the company knows
2. BEHAVIOR    → How the AI should respond
3. WORKFLOW    → How the business process must execute
4. TOOLS       → What actions the AI is allowed to perform
```

TigerDataLab combines these layers into one application architecture.

## Company AI example

```python
from tigerdatalab import create_project
from tigerdatalab.ai import OpenAIProvider

tdl = create_project("acme-support")

company = tdl.company_ai("customer-support")

company.add_knowledge(
    "returns-policy",
    "Unused products can be returned within 30 days.",
    department="support",
)

company.connect(
    OpenAIProvider(),
    "your-model",
    system="Follow company policy and answer using approved company knowledge.",
)

answer = company.ask("What is our return policy?")

print(answer.output)
print(answer.context)
```

The provider API key should come from environment configuration or a secrets manager, not from training data or source control.

---

# 6. Company AI Workflow Training

For real business automation, do not rely on a prompt alone. Define the business process explicitly.

### Example: Customer Return Workflow

```text
Customer asks for return
          ↓
Identify customer
          ↓
Retrieve order
          ↓
Check payment/order status
          ↓
Retrieve return policy
          ↓
Check eligibility
          ↓
Apply business rules
          ↓
 ┌───────────────┬────────────────┐
 │ Eligible      │ Not eligible   │
 ↓               ↓                │
Create return    Explain policy   │
request          + reason         │
 │               │                │
 └───────────────┴────────────────┘
          ↓
Escalate high-risk cases
          ↓
Generate final response
```

### Example: Invoice Dispute Workflow

```yaml
workflow: invoice_dispute
steps:
  - identify_customer
  - retrieve_invoice
  - check_payment
  - check_dispute
  - apply_policy
  - determine_resolution
  - respond_customer

conditions:
  escalation:
    if: dispute_amount > 10000
```

The important principle is that the **LLM is one component inside the workflow**, not the workflow itself.

---

# 7. RAG — Give Company AI Current Knowledge

Use RAG when the AI needs information that changes frequently or belongs to the company.

```python
from tigerdatalab.ai import Document, KnowledgeBase

kb = KnowledgeBase()

kb.add(Document(
    "finance-policy",
    "Refunds are issued within 7 business days.",
    {"department": "finance"},
))
kb.add(Document(
    "support-policy",
    "Priority customers receive 24/7 support.",
    {"department": "support"},
))

print(kb.search("refund timing", top_k=3))
print(kb.context("refund timing", top_k=3))
```

The built-in retrieval layer is dependency-light and deterministic. Production systems can place embeddings and a vector database behind the same knowledge boundary.

### RAG vs Fine-Tuning

| Need | Recommended approach |
|---|---|
| Frequently changing company information | RAG |
| Policies and documents | RAG |
| Stable response style | Fine-tuning |
| Output format | Fine-tuning / prompt / schema |
| Multi-step business process | Workflow |
| Taking actions in business systems | Approved tools/APIs |
| Measuring quality | Evaluation |

---

# 8. Company AI Tools and APIs

Company AI can use explicit, allow-listed tools rather than executing arbitrary model-generated code.

```python
from tigerdatalab.ai import Tool, ToolRegistry

registry = ToolRegistry()

registry.register(Tool(
    name="get_order",
    description="Get an order by ID",
    function=get_order,
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string"}
        },
        "required": ["order_id"],
    },
))
```

This makes actions explicit and controllable.

---

# 9. Evaluate Company AI Before Production

Do not deploy a company AI system without representative evaluation cases.

```python
from tigerdatalab.ai import evaluate

result = evaluate(
    lambda messages: "4",
    [{"prompt": "2+2?", "expected": "4"}],
)

print(result.score)
print(result.average_latency_ms)
```

For a real company system, evaluate:

- Answer accuracy
- Policy compliance
- Hallucination rate
- Workflow compliance
- Tool success rate
- Latency
- Model/version regression
- Human approval rate
- Escalation accuracy

---

# 10. Model Providers and Routing

TigerDataLab supports provider adapters including:

- OpenAI
- Anthropic
- Google Gemini
- Groq
- OpenRouter
- Mistral
- Together AI
- OpenAI-compatible endpoints

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider

router = ModelRouter()
router.add(OpenAIProvider(), "primary-model")
router.add(OpenAIProvider(), "fallback-model")
```

The router supports ordered fallback between configured targets.

---

# 11. End-to-End Company Example

A company can use TigerDataLab like this:

```text
Company CSV / Excel / Database / API
                ↓
        DATA ENGINEERING
                ↓
        Clean + Validate + PII
                ↓
          DATA ANALYTICS
                ↓
       KPIs + Insights + Reports
                ↓
          DATA SCIENCE
                ↓
       ML / Feature Preparation
                ↓
          AI DATA LAYER
                ↓
      Training Dataset + RAG Data
                ↓
          COMPANY AI LAYER
                ↓
     Knowledge + Rules + Workflow
                ↓
        Tools + Business APIs
                ↓
        AI / LLM Provider
                ↓
           EVALUATION
                ↓
        Production Company AI
```

This allows the same data foundation to serve analysts, data scientists, engineers and AI engineers instead of building disconnected pipelines for every team.

---

# Security and production principles

TigerDataLab is designed around:

- **Local-first:** data preparation does not require an LLM API.
- **Model-agnostic:** providers and training systems are adapter-based.
- **Backward compatible:** existing analytics and AI APIs remain available.
- **Reproducible:** deterministic dataset splitting and data-science seeds are supported.
- **Secure by design:** credentials stay outside datasets and lineage; tools are allow-listed.
- **Inspectable:** lineage, manifests, quality reports and evaluation provide evidence of what happened.
- **Explicit capabilities:** unsupported training operations fail clearly instead of pretending every model is trainable.
- **Human review:** high-risk production decisions should use approval gates.

## What TigerDataLab is — and is not

### TigerDataLab is

A **Data-to-AI engineering platform** that helps teams turn raw data and business processes into trustworthy analytics, training datasets, knowledge systems, workflows and AI applications.

### TigerDataLab is not

A claim that one API can modify the weights of every proprietary LLM. Hosted models can only be fine-tuned when their provider exposes a compatible training capability. Unsupported models can still be improved at the application layer through RAG, tools, workflows, routing and evaluation.

---

# Project Layout

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

# Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

CLI smoke test:

```bash
tigerdatalab analyze tests/data/sales.csv
```

# PyPI Publishing

TigerDataLab uses GitHub Actions Trusted Publishing for PyPI. A GitHub Release triggers the publication workflow after the complete test matrix passes and the distributions pass `twine check`.

For maintainers publishing a release:

```bash
git tag v4.0.0
git push origin v4.0.0
```

Then create/publish the corresponding GitHub Release. The repository's `.github/workflows/publish.yml` builds and publishes the package to PyPI using an OIDC trusted publisher, so no long-lived PyPI token is stored in the repository.

After publication:

```bash
python -m pip install --upgrade tigerdatalab
python -c "import tigerdatalab; print(tigerdatalab.__version__)"
```

# Version

**4.0.0** — Unified Data-to-AI Platform.
