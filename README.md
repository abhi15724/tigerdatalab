<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**A unified Python platform for Data Analytics, Data Science, Data Engineering, AI training data, RAG, and Company AI.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab?style=for-the-badge&logo=pypi&logoColor=white&cacheSeconds=60" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

**v4.0.0 • Python 3.10–3.13**

</div>

---

## What is TigerDataLab?

TigerDataLab connects the complete data-to-AI workflow in one Python platform:

```text
Raw Data
   ↓
Data Engineering & Quality
   ↓
Trusted Data
   ↓
Analytics / Data Science
   ↓
AI Dataset Builder
   ↓
┌──────────────────┬────────────────────┐
│ AI Training      │ Company AI         │
│ SFT / DPO / Text │ RAG + Tools        │
└──────────────────┴────────────────────┘
   ↓
Evaluation → Deployment → Production AI
```

## 👥 Who can use TigerDataLab?

| Role | What you can do |
|---|---|
| 📊 **Data Analyst** | Load data, profile datasets, analyze business data and generate insights |
| 🧪 **Data Scientist** | Explore data, correlation analysis, reproducible train/test splits and ML preparation |
| ⚙️ **Data Engineer** | Build deterministic ETL/transformation pipelines and save pipeline manifests |
| 🤖 **AI / LLM Engineer** | Build training datasets, prepare JSONL and fine-tune compatible models |
| 🏢 **Company / AI Team** | Build company knowledge bases, connect models, add workflows and create Company AI |

---

## 📊 Data Analyst Workflow

Use TigerDataLab to go from a raw CSV, Excel or Parquet file to structured analysis.

```python
import tigerdatalab as td

tiger = td.create_project("SalesAnalysis")

# Load data
df = tiger.load("sales.csv")

# Profile the dataset
profile = tiger.profile(df)
print(profile)

# Run TigerDataLab analysis
result = tiger.analyze("sales.csv")
print(result)
```

Typical workflow:

```text
CSV / Excel / Parquet
        ↓
      Load
        ↓
    Profile
        ↓
  Data Quality
        ↓
    Analysis
        ↓
 Business Insights
```

Useful for sales, finance, marketing, operations, customer, supply-chain and other business datasets.

---

## 🧪 Data Scientist Workflow

Use the built-in data-science helpers for reproducible dataset exploration and preparation.

```python
import tigerdatalab as td

tiger = td.create_project("CustomerPrediction")

df = tiger.load("customers.csv")

# Dataset overview
profile = tiger.data_science.profile(df)

# Numeric correlation matrix
correlation = tiger.data_science.correlation(df)

# Reproducible train/test split
train, test = tiger.data_science.train_test_split(
    df,
    test_size=0.2,
    seed=42,
)

print(profile)
print(correlation)
print(train.shape, test.shape)
```

Typical workflow:

```text
Dataset
   ↓
Profiling / EDA
   ↓
Correlation / Statistics
   ↓
Feature Preparation
   ↓
Train / Test Split
   ↓
ML Model
   ↓
Evaluation
```

TigerDataLab handles the data preparation layer; you can connect your preferred ML framework for model development.

---

## ⚙️ Data Engineer Workflow

Build deterministic, testable transformations with the `DataPipeline` API.

```python
import tigerdatalab as td

tiger = td.create_project("DataEngineering")
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

Typical workflow:

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
   ↓
Analytics / ML / AI
```

The pipeline executes steps in order and verifies that every transformation returns a DataFrame.

---

## 🤖 AI / LLM Engineer Workflow

Turn structured records into AI training data and train a compatible model through the pluggable training layer.

```python
import tigerdatalab as td

tiger = td.create_project("SupportAI")

# Prepare an SFT dataset
ai_project = tiger.ai_training(
    "SupportAI",
    task="sft",
)

dataset = ai_project.prepare(
    "support_training.jsonl",
    output_dir="./ai_dataset",
)

# Train a compatible model
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

The AI data layer supports training-oriented formats such as SFT/instruction, DPO, classification and text datasets, together with quality, deduplication, privacy and lineage capabilities.

### Training output

```text
ai_dataset/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md
```

For compatible local/open models, TigerDataLab can use the built-in Transformers/TRL backend. Other model families or vendors can be integrated through a custom training backend.

> **Important:** TigerDataLab is model-agnostic, but actual weight training depends on the model and compatible training backend/provider. It does not claim to modify the weights of every proprietary model.

---

## 🏢 Company AI Workflow

Use company documents and operational knowledge to build a company-specific AI layer.

```python
import tigerdatalab as td

tiger = td.create_project("AcmeAI")
company = tiger.company_ai("AcmeAI")

# Add company knowledge
company.add_knowledge(
    "HR Policy",
    "Employees receive 18 annual leaves per year.",
)

# Connect a compatible provider and model
company.connect(
    provider,
    model="your-model",
)

answer = company.ask(
    "How many annual leaves do employees receive?"
)

print(answer)
```

Company AI can combine:

```text
Company Documents
       ↓
Clean + Validate
       ↓
Knowledge Base
       ↓
RAG
       ↓
Company AI
       ↓
Tools + Workflows
       ↓
Evaluation
       ↓
Production Application
```

### RAG vs Fine-tuning

- **RAG** → current company knowledge, documents, policies and changing information.
- **Fine-tuning** → stable behavior, style, classification and task-specific output.
- **Tools** → controlled actions through APIs and business systems.
- **Workflows** → structured multi-step business processes.
- **Evaluation** → measure quality, failures and latency.

---

## 🔄 Complete End-to-End Example

A company can combine the different capabilities into one workflow:

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
        Data Analytics       Data Science
             │                     │
             └──────────┬──────────┘
                        ↓
                  TRUSTED DATA
                        ↓
               AI DATASET BUILDER
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
       Fine-tuning              RAG
       when supported        Knowledge Base
             │                     │
             └──────────┬──────────┘
                        ↓
                   COMPANY AI
                        ↓
                Tools + Workflows
                        ↓
                    Evaluation
                        ↓
                   Production
```

This means the same library can sit across the workflow instead of forcing teams to maintain unrelated data-preparation and AI-data utilities.

---

## ✨ Core Capabilities

| Area | What TigerDataLab does |
|---|---|
| 📊 Analytics | Profile, analyze and understand business data |
| ⚙️ Data Engineering | Ingest, clean, transform and build deterministic pipelines |
| 🧪 Data Science | Dataset profiling, correlations and reproducible splitting |
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

---

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

---

## 🗂️ Supported Data Workflow

```text
CSV ───────┐
Excel ─────┤
JSON/JSONL ┤
Parquet ───┤
           ↓
     TigerDataLab
           ↓
 ┌─────────┼──────────┐
 ↓         ↓          ↓
Analytics Engineering Data Science
                     ↓
                  AI Data
                     ↓
             RAG / Training
```

The unified facade supports CSV, JSON/JSONL, Excel and Parquet loading for the core data workflow.

---

## 🔒 Enterprise Principles

- No API keys stored in datasets or lineage.
- PII protection before training workflows.
- Deterministic dataset splitting and processing.
- Pluggable model and training backends.
- Controlled tool execution through allow-listed tools.
- Dataset lineage and quality reports for auditability.

---

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
