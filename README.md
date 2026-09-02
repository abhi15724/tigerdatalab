<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**A unified Python platform for Data Analytics, Data Science, Data Engineering, AI training data, RAG, and Company AI agents.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab?style=for-the-badge&logo=pypi&logoColor=white&cacheSeconds=0" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

**v4.1.0 • Python 3.10–3.13**

</div>

---

## What is TigerDataLab?

TigerDataLab connects the complete data-to-AI lifecycle in one Python platform:

```text
Raw Company Data
       ↓
Data Engineering + Quality
       ↓
Trusted Data
       ↓
Analytics + Data Science
       ↓
AI Dataset Builder
       ↓
┌───────────────────┬──────────────────────┐
│ General AI        │ Company AI Agent     │
│ Training          │ RAG + Tools + Flow   │
└───────────────────┴──────────────────────┘
       ↓
Evaluation → Application → Production AI
```

TigerDataLab is designed so teams can use the same library across analytics, engineering, machine-learning preparation and AI engineering instead of building disconnected data utilities.

## 👥 Who can use TigerDataLab?

| Role | Main use |
|---|---|
| 📊 **Data Analyst** | Load, profile, analyze and understand business datasets |
| 🧪 **Data Scientist** | EDA, correlations, reproducible train/test preparation and ML data work |
| ⚙️ **Data Engineer** | Build deterministic ETL/transformation pipelines and manifests |
| 🤖 **AI / LLM Engineer** | Build high-quality training datasets and train compatible models |
| 🏢 **AI / Automation Team** | Create company AI systems with knowledge, models, tools, workflows and evaluation |

---

# 📊 1. Data Analyst

Use TigerDataLab to move from raw business data to a structured analysis.

### Basic analysis

```python
import tigerdatalab as td

tiger = td.create_project("SalesAnalysis")

df = tiger.load("sales.csv")

profile = tiger.profile(df)
print(profile)

result = tiger.analyze("sales.csv")
print(result)
```

### Supported core files

- CSV
- JSON / JSONL
- Excel (`.xlsx`, `.xls`)
- Parquet

### Typical workflow

```text
CSV / Excel / Parquet
        ↓
       Load
        ↓
     Profile
        ↓
   Data Quality
        ↓
     Analyze
        ↓
 Business Insights
```

Useful for sales, finance, marketing, customer, operations and supply-chain datasets.

---

# 🧪 2. Data Scientist

TigerDataLab provides lightweight, reproducible helpers for dataset exploration and ML preparation.

```python
import tigerdatalab as td

tiger = td.create_project("CustomerPrediction")
df = tiger.load("customers.csv")

profile = tiger.data_science.profile(df)
correlation = tiger.data_science.correlation(df)

train, test = tiger.data_science.train_test_split(
    df,
    test_size=0.2,
    seed=42,
)

print(profile)
print(correlation)
print(train.shape, test.shape)
```

### Workflow

```text
Dataset
   ↓
Profiling / EDA
   ↓
Statistics / Correlation
   ↓
Feature Preparation
   ↓
Train / Test Split
   ↓
Your ML Framework
   ↓
Model Evaluation
```

TigerDataLab handles the data preparation layer; your preferred ML framework can handle model development.

---

# ⚙️ 3. Data Engineer

Build deterministic and testable transformations with `DataPipeline`.

```python
import tigerdatalab as td

tiger = td.create_project("CustomerETL")
df = tiger.load("raw_customers.csv")

pipeline = tiger.engineering

pipeline.add(
    "remove_duplicates",
    lambda df: df.drop_duplicates(),
)

pipeline.add(
    "remove_missing_ids",
    lambda df: df.dropna(subset=["customer_id"]),
)

pipeline.add(
    "normalize_email",
    lambda df: df.assign(
        email=df["email"].str.lower().str.strip()
    ),
)

clean_df = pipeline.run(df)
pipeline.save_manifest("pipeline_manifest.json")

print(clean_df)
```

### Workflow

```text
Raw Data
   ↓
Ingestion
   ↓
Transformation
   ↓
Cleaning
   ↓
Validation
   ↓
Trusted Data
```

Every pipeline step is executed in order and must return a DataFrame. The manifest records the configured transformation steps.

---

# 🤖 4. AI / LLM Engineer — Training Data

TigerDataLab can prepare training-oriented datasets and connect them to a compatible training backend.

### Prepare an SFT dataset

```python
import tigerdatalab as td

tiger = td.create_project("SupportAI")

ai_project = tiger.ai_training(
    "SupportAI",
    task="sft",
)

dataset = ai_project.prepare(
    "support_training.jsonl",
    output_dir="./ai_dataset",
)
```

### Train a compatible model

```python
trainer = ai_project.trainer(
    model="your-compatible-model",
    output_dir="./company-model",
)

trainer.train_sft(
    dataset,
    epochs=3,
    batch_size=2,
)
```

Install training dependencies with:

```bash
python -m pip install "tigerdatalab[train]"
```

### Training data output

```text
ai_dataset/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md
```

The AI data layer supports training-oriented tasks including SFT/instruction, DPO, classification and text, with quality, privacy, deduplication and lineage processing.

> **Model compatibility:** TigerDataLab provides a model-agnostic training interface. Actual weight training depends on the model and a compatible training backend/provider. It does not claim to modify the weights of every proprietary hosted model.

---

# 📚 5. Company Knowledge / RAG

Use the Company AI layer when information changes frequently and should be retrieved rather than baked into model weights.

```python
import tigerdatalab as td

tiger = td.create_project("AcmeAI")
company = tiger.company_ai("AcmeAI")

company.add_knowledge(
    "HR Policy",
    "Employees receive 18 annual leaves per year.",
    department="HR",
    version="2026-01",
)
```

Then connect a supported provider:

```python
from tigerdatalab.ai.providers import OpenAIProvider

provider = OpenAIProvider()
company.connect(
    provider,
    model="your-model",
)

answer = company.ask("How many annual leaves do employees receive?")
print(answer.output)
```

Supported built-in provider adapters include OpenAI-compatible providers, OpenAI, Anthropic, Gemini, Groq, OpenRouter, Mistral and Together. Credentials are read from environment variables or passed explicitly.

### RAG is best for

- Company policies
- SOPs
- Product documentation
- Current operational information
- Frequently changing business knowledge

---

# 🧠 6. Create a Company AI Agent

The main agent API is `CompanyAgent`.

It combines five controlled layers:

```text
1. PREPARE  → training data
2. TEACH    → optional model fine-tuning
3. REMEMBER → company knowledge / RAG
4. ACT      → allow-listed tools + workflows
5. PROVE    → evaluation
```

Create an agent:

```python
import tigerdatalab as td

project = td.create_project("Acme")
agent = project.company_agent("acme-ap-agent")
```

The same agent can then be configured layer by layer.

## Step 1 — Prepare company training data

```python
agent.prepare_training(
    "company_training.jsonl",
    task="sft",
    output_dir="artifacts/acme_ap",
)
```

This uses TigerDataLab's AI dataset pipeline before training.

## Step 2 — Train when supported

```python
agent.train(
    model="your-compatible-model",
    output_dir="models/acme-ap",
    epochs=3,
    batch_size=2,
)
```

You can skip fine-tuning when RAG and tools are sufficient.

## Step 3 — Give the agent company knowledge

```python
agent.add_knowledge(
    "ap_policy.txt",
    "Invoices above INR 100000 require two approvals.",
    department="Accounts Payable",
)

agent.add_knowledge(
    "vendor_policy.txt",
    "New vendors must have a valid tax identifier before activation.",
)
```

Knowledge can be updated without retraining the model.

## Step 4 — Connect an AI model

```python
from tigerdatalab.ai.providers import OpenAIProvider

provider = OpenAIProvider()

agent.connect(
    provider,
    model="your-model",
    system="You are the Acme Accounts Payable assistant. Follow company policy.",
)
```

Or use another supported provider adapter:

```python
from tigerdatalab.ai.providers import OpenRouterProvider

provider = OpenRouterProvider()
agent.connect(provider, model="your-model")
```

## Step 5 — Ask the agent

```python
result = agent.ask("Check invoice INV-10482 against the AP policy.")

print(result.output)
print(result.model)
print(result.context)
```

The runtime can combine the prompt with the company's configured knowledge and registered tool schemas.

---

# 🔧 7. Give the AI Agent Tools

Tools are explicitly registered and allow-listed. The model output is never treated as arbitrary Python code.

```python
from tigerdatalab.ai.tools import Tool


def get_invoice(invoice_id: str):
    # Replace with your ERP/database/API call.
    return {
        "invoice_id": invoice_id,
        "amount": 125000,
        "status": "pending",
    }

invoice_tool = Tool(
    name="get_invoice",
    description="Retrieve invoice information by invoice ID.",
    function=get_invoice,
    parameters={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"}
        },
        "required": ["invoice_id"],
    },
)

agent.add_tool(invoice_tool)
```

A tool can also be executed explicitly:

```python
result = agent.tools.execute(
    "get_invoice",
    {"invoice_id": "INV-10482"},
)

print(result)
```

**Security principle:** only tools that your application explicitly registers are available. Do not expose unrestricted shell, filesystem or database access to a model.

> **Current scope:** TigerDataLab provides the tool contract, registry and controlled execution primitives. An application is responsible for deciding when/how to execute a tool based on the model's output; the current `CompanyAgent` does not implement an unrestricted autonomous tool-call loop.

---

# 🔄 8. Add a Business Workflow

Company agents can be connected to deterministic workflows for structured business processes.

```python
from tigerdatalab.ai.workflows import Workflow

# Configure a Workflow using the workflow primitives provided by TigerDataLab.
workflow = Workflow(
    name="invoice_review",
)

agent.set_workflow(workflow)
```

Then run the configured workflow:

```python
result = agent.run({
    "invoice_id": "INV-10482",
})

print(result)
```

Workflows are useful for processes such as:

```text
Invoice received
      ↓
Validate invoice
      ↓
Check vendor
      ↓
Check approval policy
      ↓
Flag exception / approve
      ↓
Create business result
```

The workflow layer should remain deterministic and controlled even when an AI model is used for reasoning or classification.

---

# 📈 9. Evaluate Your AI Agent

Evaluate the connected runtime against representative test cases.

```python
records = [
    {
        "prompt": "What is the approval threshold?",
        "expected": "Invoices above INR 100000 require two approvals.",
    },
    {
        "prompt": "What does a new vendor need before activation?",
        "expected": "A valid tax identifier.",
    },
]

result = agent.evaluate(records)
print(result)
```

Evaluation should be part of the development lifecycle:

```text
Build Agent
    ↓
Test Representative Cases
    ↓
Measure Quality / Failures
    ↓
Improve Data / Knowledge / Prompt / Workflow
    ↓
Evaluate Again
```

---

# 🚀 10. Complete Company AI Agent Example

A compact end-to-end pattern looks like this:

```python
import tigerdatalab as td
from tigerdatalab.ai.providers import OpenAIProvider
from tigerdatalab.ai.tools import Tool

# 1. Create project + agent
project = td.create_project("Acme")
agent = project.company_agent("acme-ap-agent")

# 2. Prepare training data
agent.prepare_training(
    "data/ap_training.jsonl",
    task="sft",
    output_dir="artifacts/ap_dataset",
)

# 3. Optional: train a compatible model
# agent.train(
#     model="your-compatible-model",
#     output_dir="models/acme-ap",
#     epochs=3,
# )

# 4. Add current company knowledge
agent.add_knowledge(
    "ap_policy.txt",
    "Invoices above INR 100000 require two approvals.",
)

# 5. Add a controlled business tool
def get_invoice(invoice_id: str):
    return {"invoice_id": invoice_id, "amount": 125000, "status": "pending"}

agent.add_tool(Tool(
    name="get_invoice",
    description="Retrieve invoice information.",
    function=get_invoice,
    parameters={
        "type": "object",
        "properties": {"invoice_id": {"type": "string"}},
        "required": ["invoice_id"],
    },
))

# 6. Connect a model
agent.connect(
    OpenAIProvider(),
    model="your-model",
    system="You are an Accounts Payable assistant. Follow company policy.",
)

# 7. Ask the agent
answer = agent.ask("Review invoice INV-10482.")
print(answer.output)
```

This gives you the building blocks for a company-specific AI application without forcing the company to retrain a model every time a policy changes.

---

# 🏗️ 11. Recommended Architecture for Production

```text
                    COMPANY DATA
                         ↓
               ┌──────────────────┐
               │ Data Engineering │
               └────────┬─────────┘
                        ↓
                 Data Quality / PII
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
        Analytics             Data Science
             │                     │
             └──────────┬──────────┘
                        ↓
                  TRUSTED DATA
                        ↓
                AI DATASET BUILDER
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
        Fine-tuning               RAG
       when supported        Knowledge Base
             │                     │
             └──────────┬──────────┘
                        ↓
                  COMPANY AI AGENT
                        ↓
               Tools + Workflows
                        ↓
                    Evaluation
                        ↓
                 Your Application
                        ↓
                    Production
```

### When to use what?

| Requirement | Recommended layer |
|---|---|
| Understand raw business data | Analytics |
| Prepare ML data | Data Science |
| Build repeatable ETL | Data Engineering |
| Improve model behavior on stable examples | Fine-tuning |
| Give AI current company knowledge | RAG / Knowledge Base |
| Let AI interact with business systems | Tools |
| Execute repeatable multi-step processes | Workflows |
| Check AI quality | Evaluation |
| Build a complete company AI system | `CompanyAgent` |

---

# 🔐 Security & Enterprise Principles

TigerDataLab is designed around controlled AI engineering:

- PII protection before training workflows.
- API keys are not placed into datasets or lineage artifacts.
- Deterministic dataset processing and splitting.
- Deduplication and data-quality checks in the AI data pipeline.
- Explicit tool allow-listing.
- No arbitrary code execution from model output.
- Pluggable model and training backends.
- Dataset lineage and quality reports.

For production deployments, add your own authentication, authorization, secrets management, audit logging, rate limits, network controls and monitoring around the application.

---

# ✨ Core Capabilities

| Area | Capability |
|---|---|
| 📊 Analytics | Profile and analyze business data |
| ⚙️ Data Engineering | Deterministic ingestion and transformation pipelines |
| 🧪 Data Science | Profiling, correlation and reproducible splitting |
| 🧠 AI Data | SFT, instruction, DPO, classification and text datasets |
| 🔐 Privacy | PII-aware training-data processing |
| 🧹 Quality | Validation, deduplication and quality reporting |
| 📚 RAG | Company knowledge retrieval |
| 🤖 Training | Compatible model training through pluggable backends |
| 🔀 Routing | Provider/model routing primitives |
| 🔧 Tools | Explicitly registered business tools |
| 🔄 Workflows | Structured business processes |
| 📈 Evaluation | Test and measure AI behavior |
| 🧾 Lineage | Track AI dataset creation |
| 🏢 Company Agent | Combine data, knowledge, model, tools, workflows and evaluation |

---

# 📦 Installation

Basic installation:

```bash
python -m pip install tigerdatalab
```

AI training support:

```bash
python -m pip install "tigerdatalab[train]"
```

All optional capabilities:

```bash
python -m pip install "tigerdatalab[all]"
```

Verify installation:

```bash
python -c "import tigerdatalab as td; print(td.__version__)"
```

---

# 🗂️ Unified Data-to-AI API

The main entry point is:

```python
import tigerdatalab as td

tiger = td.create_project("MyProject")
```

Then choose the capability you need:

```python
# Data Analytics
df = tiger.load("data.csv")
profile = tiger.profile(df)
result = tiger.analyze("data.csv")

# Data Engineering
pipeline = tiger.engineering

# Data Science
train, test = tiger.data_science.train_test_split(df)

# AI Training
ai_project = tiger.ai_training("SupportAI", task="sft")

# Company AI
company = tiger.company_ai("AcmeAI")

# Company AI Agent
agent = tiger.company_agent("AcmeAgent")
```

---

# 📚 Project Structure

```text
tigerdatalab/
├── core/                 # analytics and core data operations
├── ai/
│   ├── datasets.py       # AI dataset handling
│   ├── dedup.py          # deterministic deduplication
│   ├── pipeline.py       # AI data pipeline
│   ├── privacy.py        # privacy / PII processing
│   ├── quality.py        # data quality
│   ├── schema.py         # dataset schemas
│   ├── training.py       # universal training interface
│   ├── providers.py      # model provider adapters
│   ├── rag.py            # knowledge base / retrieval
│   ├── tools.py          # controlled tool registry
│   ├── workflows.py      # workflow primitives
│   ├── evaluation.py     # evaluation
│   ├── router.py         # model routing
│   ├── system.py         # Company AI runtime
│   └── agent.py          # CompanyAgent lifecycle
├── platform.py           # unified public facade
└── ...
```

---

# ⚠️ Scope and Limitations

TigerDataLab provides the engineering primitives and orchestration layer. A production application still needs infrastructure around it.

Current CompanyAgent does **not** automatically provide:

- A hosted deployment server.
- Automatic unrestricted autonomous tool-call loops.
- Live ERP/CRM integrations out of the box.
- Automatic ingestion of every PDF/DOCX/Excel document format into the knowledge base.
- Built-in observability dashboards.
- Automatic weight modification for proprietary hosted LLMs.

These boundaries are intentional: application owners control deployment, credentials, business-system access and execution policies.

---

# 🔗 Resources

- [GitHub Repository](https://github.com/abhi15724/tigerdatalab)
- [PyPI Package](https://pypi.org/project/tigerdatalab/)
- [Releases](https://github.com/abhi15724/tigerdatalab/releases)
- [License](LICENSE)

---

<div align="center">

**🐯 TigerDataLab — Build trusted data. Teach AI. Ship intelligence.**

</div>
