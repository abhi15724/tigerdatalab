<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**One Python platform for Data Analytics, Data Science, Data Engineering, AI training data, LLM fine-tuning orchestration, Company AI, RAG, agents, tools, workflows and evaluation.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab.svg?style=for-the-badge&logo=pypi&logoColor=white&cacheSeconds=60" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/tigerdatalab"><img src="https://api.pepy.tech/badge/tigerdatalab/month?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI monthly downloads"></a>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

**v4.1.1 • Python 3.10–3.13**

[English README](README.md) · [हिंदी README](README.hi.md)

</div>

---

## What is TigerDataLab?

TigerDataLab is a **data-to-AI engineering layer**. It helps a team move from raw business data to trusted datasets, AI training artifacts and production-oriented AI applications without locking the application to one model vendor.

```text
RAW DATA
   ↓
INGEST → PROFILE → QUALITY → CLEAN → TRANSFORM
   ↓
TRUSTED DATA
   ↓
AI DATASET BUILDER
   ↓
TRAIN / FINE-TUNE ────────┐
   │                       │
   ▼                       ▼
OPEN MODEL              COMPANY AI
TRL / Transformers      RAG + Knowledge
PEFT / LoRA             Tools + Workflows
   │                       │
   └───────────┬───────────┘
               ▼
          EVALUATION
               ↓
        PRODUCTION AI
```

TigerDataLab does **not** claim that every proprietary hosted model can have its weights modified. Training depends on model architecture, licensing, hardware and the selected training backend. The platform keeps the data/training contract stable while allowing compatible backends to be swapped in.

---

## Who can use it?

| User | Example work |
|---|---|
| 📊 Data Analyst | Cleaning, profiling, KPIs, trends, insights, dashboards and reports |
| 🧪 Data Scientist | Data preparation, reproducible splits, analysis and ML-ready datasets |
| ⚙️ Data Engineer | ETL transformations, deterministic pipelines and manifests |
| 🤖 AI/LLM Engineer | SFT/DPO/instruction datasets, PII protection, deduplication, lineage and training |
| 🏢 Enterprise AI Team | Company knowledge, RAG, model routing, tools, workflows and evaluation |
| 💼 Business Team | Turn SOPs, policies and operational data into AI-ready workflows |

---

# Installation

### Standard

```bash
python -m pip install tigerdatalab
```

### AI/LLM training

```bash
python -m pip install "tigerdatalab[train]"
```

The training extra includes the optional Hugging Face/Transformers/TRL/PEFT ecosystem. Pin and test dependency versions in production environments.

---

# Output Formats

TigerDataLab returns structured Python objects during interactive workflows and writes standard machine-readable artifacts for automated pipelines.

| Operation | Output format | Typical output |
|---|---|---|
| Data loading / analysis | Python objects / DataFrames | `DataFrame`, profile and analysis result objects |
| Data cleaning | CSV / Excel | `.csv`, `.xlsx` |
| Data engineering | DataFrame + JSON | transformed `DataFrame`, `pipeline_manifest.json` |
| AI training data | JSONL | `train.jsonl`, `validation.jsonl`, `test.jsonl` |
| Dataset quality | JSON | `quality_report.json` |
| Dataset lineage | JSON | `lineage.json` |
| Dataset documentation | Markdown | `dataset_card.md` |
| Model evaluation | JSON | `evaluation_report.json` |
| Run metadata | JSON | `run_manifest.json` |
| Reports / dashboards | PDF / HTML | business reports and dashboard artifacts |
| Company AI / RAG | Python result objects | answer/output and retrieved context |
| Model training | Model/backend-specific | model or adapter artifacts |

### Common AI training output

```text
./artifacts/<run-name>/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
├── dataset_card.md
├── evaluation_report.json
├── run_manifest.json
└── model/
    └── model or adapter artifacts
```

JSONL is used for training datasets because it stores one training example per line and works well with streaming, validation and common LLM training pipelines. The exact schema depends on the selected task or adapter.

---

# 1. Data Analyst

```python
import tigerdatalab as td

project = td.create_project("SalesAnalysis")
df = project.load("sales.csv")

profile = project.profile(df)
analysis = project.analyze("sales.csv")

print(profile)
print(analysis.summary)
```

Typical workflow:

```text
CSV / Excel / Parquet
        ↓
TigerDataLab
        ↓
Profile + Quality
        ↓
KPI / trend / insight analysis
        ↓
Dashboard / report artifacts
```

Use the returned structured objects in your Python application instead of parsing terminal output.

---

# 2. Data Quality & Cleaning

```python
quality = td.quality_check("sales.csv")

cleaned = td.clean_file(
    "raw_customers.xlsx",
    output_path="clean_customers.xlsx",
)
```

TigerDataLab's AI-data pipeline also performs privacy-oriented masking, deduplication, validation and quality measurement before training-data export.

---

# 3. Data Scientist

```python
import tigerdatalab as td

project = td.create_project("CustomerPrediction")
df = project.load("customers.csv")

profile = project.data_science.profile(df)
correlation = project.data_science.correlation(df)

train, test = project.data_science.train_test_split(
    df,
    test_size=0.2,
    seed=42,
)
```

The split is reproducible with the same seed. Continue with your preferred ML framework after TigerDataLab prepares the data.

---

# 4. Data Engineer

Build deterministic ETL transformations:

```python
import tigerdatalab as td

project = td.create_project("CustomerETL")

df = project.load("raw_customers.csv")

pipeline = project.engineering

pipeline.add("remove_duplicates", lambda x: x.drop_duplicates())
pipeline.add("remove_missing_ids", lambda x: x.dropna(subset=["customer_id"]))
pipeline.add(
    "normalize_email",
    lambda x: x.assign(email=x["email"].str.lower().str.strip()),
)

clean_df = pipeline.run(df)
pipeline.save_manifest("pipeline_manifest.json")
```

Output:

```text
clean_df
pipeline_manifest.json
```

The manifest records the configured transformation sequence for reproducibility and auditing.

---

# 5. AI Training Data

Suppose your company has `support.csv`:

```csv
question,answer,department
How do I reset my password?,Open Settings and select Reset Password.,support
What is the return policy?,Unused products may be returned within 30 days.,support
How do I process an invoice?,Follow the approved AP workflow.,finance
```

Prepare it for supervised fine-tuning:

```python
import tigerdatalab as td

project = td.create_project("SupportAI")

ai = project.ai_training(
    "support-model",
    source="support.csv",
    task="sft",
    output_dir="./support-ai-run",
)

ai.clean_data()
validation = ai.validate_data()
ai.convert_to_sft()
splits = ai.split_dataset(
    train_ratio=0.8,
    validation_ratio=0.1,
    strategy="hash",
)

print(validation)
print({name: len(records) for name, records in splits.items()})
```

The pipeline performs:

```text
Raw records
   ↓
PII-oriented masking
   ↓
Format conversion
   ↓
Deduplication
   ↓
Validation
   ↓
Quality measurement
   ↓
Deterministic train/validation/test split
```

---

# 6. Complete AI/LLM Training Pipeline

The end-to-end API directly maps to the six stages:

```text
clean_data()
      ↓
validate_data()
      ↓
convert_to_sft()
      ↓
split_dataset()
      ↓
train_model()
      ↓
evaluate_model()
```

### Complete example

```python
import tigerdatalab as td

project = td.create_project("AcmeSupport")

ai = project.ai_training(
    "acme-support",
    source="company_support.csv",
    task="sft",
    output_dir="./artifacts/acme-support",
)

ai.clean_data()
validation = ai.validate_data()
ai.convert_to_sft()
splits = ai.split_dataset(
    train_ratio=0.8,
    validation_ratio=0.1,
    strategy="hash",
)

ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="lora",
    epochs=2,
    batch_size=2,
    learning_rate=1e-4,
)

def model(prompt: str) -> str:
    return "your model response"

result = ai.evaluate_model(model)
print("Score:", result.score)
print("Latency:", result.average_latency_ms)
print(ai.export_run_manifest())
```

### What you get

```text
artifacts/acme-support/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
├── dataset_card.md
├── evaluation_report.json
└── run_manifest.json
```

The training backend writes model artifacts under the configured model output directory. Exact files depend on the model and backend.

---

# 7. Open-source Model Training

The built-in training backend uses **Hugging Face Transformers + Datasets + TRL** for compatible causal language models.

For parameter-efficient fine-tuning:

```python
ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="lora",
    lora_r=16,
    lora_alpha=32,
    lora_dropout=0.05,
)
```

QLoRA-style 4-bit loading is also available where the model, hardware and installed quantization stack support it:

```python
ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="qlora",
)
```

**Training is not the same as inference.** An API such as OpenRouter can generate or evaluate responses, but local/open-model weight updates require a compatible training backend and compute.

---

# 8. OpenRouter and Other AI Providers

TigerDataLab is **not locked to OpenAI**.

For Company AI inference, you can use provider adapters including:

```text
OpenAI
Anthropic
Google Gemini
Groq
OpenRouter
Mistral
Together AI
OpenAI-compatible APIs
Custom providers
```

Example with OpenRouter:

```python
from tigerdatalab.ai.providers import OpenRouterProvider

company.connect(
    OpenRouterProvider(),
    model="YOUR_OPENROUTER_MODEL",
    system="You are the company assistant. Follow company policy.",
)
```

Example with OpenAI:

```python
from tigerdatalab.ai.providers import OpenAIProvider

company.connect(
    OpenAIProvider(),
    model="YOUR_OPENAI_MODEL",
    system="You are the company assistant. Follow company policy.",
)
```

The application, knowledge layer and workflow can remain the same while the provider changes.

Provider credentials should normally be supplied through environment variables such as:

```bash
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
GROQ_API_KEY=...
MISTRAL_API_KEY=...
TOGETHER_API_KEY=...
```

Use the credential name documented for the provider/version you install.

---

# 9. Company AI / RAG

Use RAG when company information changes frequently and should not require retraining.

```python
import tigerdatalab as td

project = td.create_project("Acme")
company = project.company_ai("AcmeAssistant")

company.add_knowledge(
    "AP Policy",
    "Invoices above INR 100000 require two approvals.",
    department="finance",
)

company.add_knowledge(
    "Return Policy",
    "Unused products may be returned within 30 days.",
    department="support",
)
```

Then connect a model and ask:

```python
company.connect(
    provider,
    model="YOUR_MODEL",
    system="You are the Acme company assistant. Follow company policy.",
)

result = company.ask("What is the return policy?")
print(result.output)
print(result.context)
```

Conceptually:

```text
Company policies / SOPs
          ↓
TigerDataLab Knowledge Base
          ↓
Relevant context
          ↓
LLM
          ↓
Grounded company answer
```

---

# 10. Company AI Agent

Create an agent for a business process:

```python
project = td.create_project("Acme")
agent = project.company_agent("acme-ap-agent")
```

An enterprise agent can combine:

```text
Company training data
        +
Company knowledge / RAG
        +
Model provider
        +
Allow-listed tools
        +
Business workflows
        +
Evaluation
```

Example business use case:

```text
Invoice received
      ↓
Retrieve invoice
      ↓
Check company policy
      ↓
Classify / reason
      ↓
Flag exception
      ↓
Human approval
      ↓
Business system
```

For safety, tools should be explicit and allow-listed. Do not give an LLM unrestricted shell, filesystem, database-write or arbitrary-code access.

---

# 11. Evaluation

Evaluation can be run against any callable model:

```python
from tigerdatalab.ai import evaluate

records = [
    {
        "prompt": "What is the return policy?",
        "expected": "Unused products may be returned within 30 days.",
    },
]

result = evaluate(model, records)

print(result.total)
print(result.passed)
print(result.failed)
print(result.score)
print(result.average_latency_ms)
```

Use a custom scorer for domain-specific checks:

```python
def scorer(output, record):
    return "30 days" in output

result = evaluate(model, records, scorer=scorer)
```

Recommended lifecycle:

```text
Train / configure
      ↓
Evaluate
      ↓
Find failures
      ↓
Improve data / knowledge / workflow
      ↓
Evaluate again
      ↓
Release
```

---

# 12. Custom Training Backends

TigerDataLab does not force every organization to use the built-in Transformers backend.

```python
from tigerdatalab.ai import CallableTrainingBackend, TrainingCapabilities

def enterprise_train(request):
    return {"status": "submitted", "model": request.model}

backend = CallableTrainingBackend(
    enterprise_train,
    name="enterprise-training",
    capabilities=TrainingCapabilities(
        supervised_fine_tuning=True,
        preference_tuning=True,
        local=False,
    ),
)

ai.train_model(
    model="enterprise-model",
    backend=backend,
)
```

This makes TigerDataLab useful when the customer's training infrastructure is proprietary, hosted internally or provided by another vendor.

---

# 13. Model Routing

Use `ModelRouter` when an application needs multiple model targets:

```python
from tigerdatalab.ai import ModelRouter, OpenRouterProvider

router = ModelRouter()
router.add(OpenRouterProvider(), "model-a")
router.add(OpenRouterProvider(), "model-b")
```

The routing layer can support provider/model selection and fallback strategies while keeping application code independent from one model target.

---

# 14. Production Architecture

```text
                         ENTERPRISE DATA
                               ↓
                    ┌────────────────────┐
                    │ TigerDataLab       │
                    │ Data Layer         │
                    └─────────┬──────────┘
                              ↓
                  Quality + PII + Lineage
                              ↓
                      Trusted Data
                              ↓
                   AI Dataset Builder
                              ↓
                ┌─────────────┴─────────────┐
                ↓                           ↓
          Model Training                Company AI
          TRL / Custom                  RAG / Knowledge
                ↓                           ↓
          Model / Adapter              Tools / Workflow
                └─────────────┬─────────────┘
                              ↓
                         Evaluation
                              ↓
                         AI Application
```

TigerDataLab is the Python data/AI layer. A production application remains responsible for authentication, authorization, secrets management, network controls, database permissions, deployment infrastructure and monitoring.

---

# 15. Security Principles

For enterprise data:

- use least-privilege access
- detect/mask sensitive data before training where appropriate
- maintain dataset lineage
- use explicit tool allow-lists
- separate training, validation and test data
- keep credentials outside source code
- define retention and deletion rules
- review licenses and data rights
- audit model and workflow behavior before production

For highly sensitive deployments, evaluate customer-controlled storage, private networking/VPC, on-premise execution and enterprise security/compliance requirements separately.

---

# 16. Important Scope

### What TigerDataLab does

- Data analytics and profiling
- Data quality and cleaning
- Data engineering pipelines
- AI training-data preparation
- PII-oriented masking
- Deduplication and validation
- Deterministic dataset splitting
- SFT/instruction/DPO/classification/text dataset adapters
- Training orchestration
- Transformers + TRL SFT backend
- PEFT/LoRA support
- Custom training backends
- Company knowledge/RAG primitives
- AI agents, tools and workflows
- Model routing
- Evaluation
- Dataset/model run artifacts and lineage

### What it does not promise

TigerDataLab cannot modify the weights of literally every model. Proprietary APIs, model licenses, architectures and hardware requirements differ. The universal architecture means the **TigerDataLab workflow and backend contract remain stable**, while a compatible model/training system is selected underneath.

---

# 17. Project Output Example

A typical AI training run can produce:

```text
support-ai-run/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
├── dataset_card.md
├── evaluation_report.json
├── run_manifest.json
└── model/
    └── model or adapter artifacts
```

These artifacts let a team inspect what data was produced, how it was processed, how it was split and how the model evaluation performed.

---

# 18. Quick API Reference

```python
import tigerdatalab as td

# Data
project = td.create_project("MyProject")
df = project.load("data.csv")
profile = project.profile(df)
analysis = project.analyze("data.csv")

# Engineering
pipeline = project.engineering
pipeline.add("step", lambda df: df)
result = pipeline.run(df)
pipeline.save_manifest("pipeline.json")

# AI training
ai = project.ai_training(
    "MyAI",
    source="training.jsonl",
    task="sft",
    output_dir="./run",
)
ai.clean_data()
ai.validate_data()
ai.convert_to_sft()
ai.split_dataset()
ai.train_model(model="YOUR_COMPATIBLE_MODEL", method="lora")
ai.evaluate_model(model_callable)
ai.export_run_manifest()

# Company AI
company = project.company_ai("CompanyAI")
company.add_knowledge("policy", "Company policy text")
company.connect(provider, model="YOUR_MODEL")
answer = company.ask("Ask a company question")

# Company agent
agent = project.company_agent("CompanyAgent")
```

---

# License

See [`LICENSE`](LICENSE).

# Links

- [GitHub](https://github.com/abhi15724/tigerdatalab)
- [PyPI](https://pypi.org/project/tigerdatalab/)
- [Hindi README](README.hi.md)
- [End-to-end AI training guide](docs/end-to-end-ai-training.md)
- [CI](https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml)

<div align="center">

**🐯 TigerDataLab — From Raw Data to Production AI**

</div>
