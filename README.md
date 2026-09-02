<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**A unified Python platform for Data Analytics, Data Science, Data Engineering, AI training data, RAG, and Company AI.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab?style=for-the-badge&logo=pypi&logoColor=white&cacheSeconds=60" alt="PyPI version"></a>
  <a href="https://img.shields.io/pypi/pyversions/tigerdatalab"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

**v4.0.0 • Python 3.10–3.13**

</div>

---

## What is TigerDataLab?

TigerDataLab connects the complete AI and data workflow:

```text
Raw Company Data
      ↓
Data Engineering & Quality
      ↓
Trusted Data
      ↓
AI Dataset Builder
      ↓
┌───────────────┬────────────────┐
│ AI Training   │ Company AI     │
│ SFT / DPO     │ RAG + Tools    │
└───────────────┴────────────────┘
      ↓
Evaluation → Deployment → Production AI
```

## ✨ Core Capabilities

| Area | What TigerDataLab does |
|---|---|
| 📊 Analytics | Profile, analyze and understand business data |
| ⚙️ Data Engineering | Ingest, clean, validate and transform datasets |
| 🧠 AI Data | Build SFT, instruction, DPO, classification and text datasets |
| 🔐 Privacy | Mask PII before AI training and processing |
| 🧹 Quality | Deduplicate, validate, score and filter training data |
| 📚 RAG | Build searchable company knowledge bases |
| 🤖 Training | Train compatible models through pluggable backends |
| 🔀 Routing | Route AI requests across compatible model providers |
| 🔧 Tools | Connect AI to controlled business tools and APIs |
| 🔄 Workflows | Build structured company AI processes |
| 📈 Evaluation | Measure quality, failures and latency |
| 🧾 Lineage | Track how AI datasets were created |

## 📦 Installation

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

## 🚀 Quick Start

```python
import tigerdatalab as td

# Create a company AI project
project = td.create_project("AcmeAI", type="company_ai")

# Build and prepare AI training data
# Then connect a compatible training backend,
# knowledge base, tools, workflows and evaluation.
```

## 🏢 Company AI Workflow

```text
Company Data
    ↓
Clean + Validate + Protect
    ↓
AI Training Dataset ─────→ Fine-tuning (when supported)
    │
    └────────────────────→ RAG Knowledge Base
                              ↓
                         Company AI
                              ↓
                    Tools + Workflows
                              ↓
                         Evaluation
                              ↓
                         Deployment
```

### RAG vs Fine-tuning

- **RAG** → current company knowledge, documents, policies and changing information.
- **Fine-tuning** → stable behavior, style, classification and task-specific output.
- **Tools** → controlled actions through APIs and business systems.
- **Evaluation** → verify that the AI actually performs correctly.

> TigerDataLab uses a model-agnostic architecture. Actual fine-tuning depends on the model and compatible training backend/provider.

## 🧪 AI Dataset Example

TigerDataLab can turn company records into training-ready JSONL:

```json
{"instruction":"How many annual leaves are allowed?","response":"Employees receive 18 annual leaves per year."}
```

And produce:

```text
ai_dataset/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md
```

## 🧩 Architecture

```text
                    TIGERDATALAB
                         │
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
   Analytics        Data Science     Engineering
       └─────────────────┼─────────────────┘
                         ↓
                   AI DATA LAYER
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
        AI TRAINING             COMPANY AI
             ↓                       ↓
      Compatible Models        RAG + Tools
             └───────────┬───────────┘
                         ↓
                    Evaluation
                         ↓
                    Production AI
```

## 🔒 Enterprise Principles

- No API keys stored in datasets or lineage.
- PII protection before training workflows.
- Deterministic dataset splitting and processing.
- Pluggable model/training backends.
- Controlled tool execution through allow-listed tools.
- Dataset lineage and quality reports for auditability.

## 📚 Documentation

- [English README](README.md)
- [हिंदी README](README.hi.md)
- [GitHub Repository](https://github.com/abhi15724/tigerdatalab)
- [PyPI Package](https://pypi.org/project/tigerdatalab/)
- [v4.0.0 Release](https://github.com/abhi15724/tigerdatalab/releases/tag/v4.0.0)

## 📄 License

See [LICENSE](LICENSE).

<div align="center">

**🐯 TigerDataLab — Build trusted data. Teach AI. Ship intelligence.**

</div>
