<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**A unified Data + AI engineering platform for Data Analytics, Data Science, Data Engineering, AI Training, and Company AI workflow training.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

<p>
  <a href="README.md">🇬🇧 English</a> &nbsp;•&nbsp;
  <a href="README.hi.md">🇮🇳 हिंदी</a>
</p>

</div>

---

## 🚀 What is TigerDataLab?

TigerDataLab connects the complete journey from **business data → trusted data → analytics → ML preparation → AI training data → company knowledge → workflows → AI applications**.

```text
                         🐯 TIGERDATALAB
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   📊 ANALYTICS          🧪 DATA SCIENCE       ⚙️ ENGINEERING
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ↓
                         🧠 AI DATA LAYER
                               │
                    ┌──────────┴──────────┐
                    ↓                     ↓
             🤖 AI TRAINING        🏢 COMPANY AI
                    │                     │
             SFT / DPO / Text      RAG / Rules / Workflow
             Classification        Tools / APIs / Evaluation
                    │                     │
                    └──────────┬──────────┘
                               ↓
                         🌐 AI / LLM LAYER
                               ↓
                       📈 EVALUATION
                               ↓
                      🚀 PRODUCTION AI
```

---

## ✨ Five Teams. One Platform.

| 👤 Role | What you can do |
|---|---|
| 📊 **Data Analyst** | Profile data, quality checks, KPIs, trends, insights, dashboards and reports |
| 🧪 **Data Scientist** | Explore datasets, reproducible splits, correlations and ML-ready preparation |
| ⚙️ **Data Engineer** | Build deterministic ETL pipelines, transformations and pipeline manifests |
| 🤖 **AI / ML Engineer** | Build SFT, DPO, classification and text datasets; PII masking, deduplication, validation and export |
| 🏢 **Company AI Builder** | Connect company knowledge, RAG, business rules, workflows, approved tools/APIs and evaluation |

**One data foundation. Multiple teams. One AI lifecycle.**

---

# 📦 Installation

```bash
python -m pip install tigerdatalab
```

### AI training capabilities

```bash
python -m pip install "tigerdatalab[train]"
```

### Full optional capabilities

```bash
python -m pip install "tigerdatalab[all]"
```

---

# ⚡ Quick Start

```python
from tigerdatalab import create_project

tdl = create_project("my-company")

result = tdl.analyze("sales.xlsx")

print(result.summary())
print(result.kpis())
```

The same project can support analytics, engineering, data science, AI training and Company AI workflows.

---

# 📊 1. Data Analyst

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

### Use cases

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

# 🧪 2. Data Scientist

Use TigerDataLab before model development to understand and prepare data.

```python
frame = tdl.load("customers.csv")

profile = tdl.profile(frame)
print(profile)

train, test = tdl.data_science.train_test_split(
    frame,
    test_size=0.2,
    seed=42,
)

correlation = tdl.data_science.correlation(train)
print(correlation)
```

```text
Raw Dataset
    ↓
Profile
    ↓
Quality Check
    ↓
Clean / Transform
    ↓
Reproducible Split
    ↓
Statistical / Feature Analysis
    ↓
Your ML Framework
```

TigerDataLab focuses on the data preparation layer; connect the resulting data to your preferred ML framework.

---

# ⚙️ 3. Data Engineer

Build deterministic, testable data transformations.

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

```text
CSV / Excel / JSON / Parquet
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
   Analytics / ML / AI
```

---

# 🤖 4. AI Training — Build Better Training Data

TigerDataLab provides the **AI data and training layer** between raw data and a compatible training system.

```text
Raw Examples
     ↓
   Ingest
     ↓
Task Formatting
     ↓
 PII Detection
     ↓
 PII Masking
     ↓
Deduplication
     ↓
Schema Validation
     ↓
 Quality Checks
     ↓
Train / Val / Test
     ↓
 JSONL Export
     ↓
Training Backend
```

### Supported dataset styles

| Dataset | Typical structure |
|---|---|
| **SFT** | Prompt / response or chat examples |
| **DPO** | Prompt + preferred + rejected response |
| **Classification** | Text + label |
| **Instruction** | Instruction + input + output |
| **Text** | General text examples |

### Example

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

### Data quality layer

✅ Schema validation  
✅ PII detection and masking  
✅ Deduplication  
✅ Quality checks  
✅ Deterministic dataset splits  
✅ Dataset lineage  
✅ Dataset cards  
✅ Quality reports  
✅ JSONL export

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

TigerDataLab is model-agnostic through training adapters. It does **not** claim that every proprietary hosted LLM can have its weights modified.

---

# 🏢 5. Company AI — Teach AI Your Business

Company AI is more than fine-tuning a model.

```text
┌──────────────────────────────────────────────┐
│             COMPANY AI SYSTEM                │
├──────────────────────────────────────────────┤
│ 🧠 KNOWLEDGE  → What the company knows       │
│ 🎯 BEHAVIOR   → How the AI should respond    │
│ 🔄 WORKFLOW   → How the process must run     │
│ 🔐 TOOLS      → What actions are allowed     │
└──────────────────────────────────────────────┘
```

### Example

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
    system="Follow company policy and use approved company knowledge.",
)

answer = company.ask("What is our return policy?")
print(answer.output)
```

---

# 🔄 Company AI Workflow Training

For real business automation, **do not rely on a prompt alone**. Define the business process explicitly.

### Customer Return Workflow

```text
Customer Request
       ↓
Identify Customer
       ↓
Retrieve Order
       ↓
Check Payment / Order Status
       ↓
Retrieve Company Policy
       ↓
Check Eligibility
       ↓
Apply Business Rules
       ↓
 ┌───────────────┬────────────────┐
 │   Eligible    │  Not Eligible  │
 ↓               ↓                │
Create Return    Explain Policy   │
 │               │                │
 └───────────────┴────────────────┘
       ↓
Escalate High-Risk Cases
       ↓
Final Response
```

### Invoice dispute workflow

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

> **The LLM is a component inside the workflow — not the workflow itself.**

---

# 🔎 RAG — Give Company AI Current Knowledge

Use RAG when the AI needs changing company information, policies or documents.

```python
from tigerdatalab.ai import Document, KnowledgeBase

kb = KnowledgeBase()

kb.add(Document(
    "finance-policy",
    "Refunds are issued within 7 business days.",
    {"department": "finance"},
))

print(kb.context("refund timing", top_k=3))
```

Production systems can place embeddings and a vector database behind the knowledge boundary.

### RAG vs Fine-Tuning vs Workflow

| Requirement | Recommended approach |
|---|---|
| Frequently changing company information | 🔎 RAG |
| Policies and documents | 🔎 RAG |
| Stable response behavior | 🧠 Fine-tuning |
| Output format | 🧠 Fine-tuning / prompt / schema |
| Multi-step business process | 🔄 Workflow |
| Taking business-system actions | 🔐 Approved tools/APIs |
| Measuring quality | 📈 Evaluation |

---

# 🔐 Tools, APIs and Safety

Company AI should use explicit, allow-listed tools rather than arbitrary model-generated code.

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

### Security principles

- 🔑 Keep API keys outside source code and datasets.
- 🛡️ Use environment variables or a secrets manager.
- 🔒 Allow-list tools and business actions.
- 👤 Use human approval for high-risk decisions.
- 🧾 Keep dataset lineage and evaluation evidence.
- 🚫 Never treat arbitrary model output as executable Python or shell code.

---

# 📈 Evaluate Before Production

```python
from tigerdatalab.ai import evaluate

result = evaluate(
    lambda messages: "4",
    [{"prompt": "2+2?", "expected": "4"}],
)

print(result.score)
print(result.average_latency_ms)
```

For a company system, evaluate:

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

# 🌐 Supported Model Providers

TigerDataLab includes provider adapters for:

**OpenAI · Anthropic · Google Gemini · Groq · OpenRouter · Mistral · Together AI · OpenAI-compatible endpoints**

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider

router = ModelRouter()
router.add(OpenAIProvider(), "primary-model")
router.add(OpenAIProvider(), "fallback-model")
```

---

# 🏗️ End-to-End Data → AI Architecture

```text
Company CSV / Excel / Database / API
                ↓
        ⚙️ DATA ENGINEERING
                ↓
       Clean + Validate + PII
                ↓
         📊 DATA ANALYTICS
                ↓
       KPIs + Insights + Reports
                ↓
         🧪 DATA SCIENCE
                ↓
       ML / Feature Preparation
                ↓
         🤖 AI DATA LAYER
                ↓
     Training Dataset + RAG Data
                ↓
        🏢 COMPANY AI LAYER
                ↓
      Knowledge + Rules + Workflow
                ↓
         Tools + Business APIs
                ↓
          🌐 AI / LLM Provider
                ↓
           📈 EVALUATION
                ↓
       🚀 PRODUCTION COMPANY AI
```

---

# 🧩 Architecture Principles

| Principle | TigerDataLab approach |
|---|---|
| **Local-first** | Data preparation does not require an LLM API |
| **Model-agnostic** | Provider and training adapters |
| **Reproducible** | Deterministic dataset splitting and seeds |
| **Secure** | Secrets outside datasets; allow-listed tools |
| **Inspectable** | Lineage, manifests, quality reports and evaluation |
| **Backward compatible** | Existing analytics APIs remain available |
| **Explicit capabilities** | Unsupported training operations fail clearly |

---

# 📁 Project Structure

```text
tigerdatalab/
├── analytics/          # Business analytics
├── dashboard/          # Dashboard generation
├── dataops/            # Data operations
├── insights/           # Insight generation
├── ai/                 # Training, RAG, providers, tools, workflows
├── cli/                # Command-line interface
├── core.py             # Core analytics API
├── platform.py         # Unified Data-to-AI project API
└── config.py           # Package configuration
```

---

# 🧪 Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

CI tests Python 3.10, 3.11 and 3.12 and runs the CLI smoke test.

---

# 🌍 Read TigerDataLab in Your Language

The primary documentation is maintained in English, with a Hindi translation available:

- 🇬🇧 **English:** [README.md](README.md)
- 🇮🇳 **हिंदी:** [README.hi.md](README.hi.md)

More translations can be added as `README.<language>.md` files while keeping the English README as the canonical technical reference.

---

# 📜 Important Scope

TigerDataLab is a **Data-to-AI engineering platform**. It helps teams turn raw data and business processes into trustworthy analytics, training datasets, company knowledge, workflows and AI applications.

It is **not** a claim that one API can modify the weights of every proprietary LLM. Hosted models can only be fine-tuned when their provider exposes compatible training capabilities. Unsupported models can still be improved at the application layer through RAG, tools, workflows, routing and evaluation.

---

<div align="center">

## 🐯 Build Data. Teach AI. Automate Work.

**TigerDataLab 4.0.0**

</div>
