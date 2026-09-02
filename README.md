# TigerDataLab

**TigerDataLab** is a local-first **Data Analytics + Data Quality + Visualization + Business Intelligence + DataOps + AI Training Data + LLM Fine-Tuning** platform for Python. It complements pandas, NumPy, DuckDB, Plotly, Hugging Face Datasets, Transformers and TRL rather than replacing them.

> **Analyze. Clean. Understand. Prepare. Fine-tune.**

## 🚀 What's new in v3.0.7

TigerDataLab v3.0.7 brings the project together as an end-to-end data-to-model workflow:

- AI training-data preparation for **SFT, conversational, DPO, classification and text** datasets
- Schema validation, quality scoring, deduplication and deterministic dataset splitting
- Local **PII detection and deterministic masking** before training export
- Dataset lineage and dataset-card style metadata
- JSONL training-data export
- Optional Hugging Face + TRL supervised fine-tuning orchestration
- Existing analytics, DataOps, large-data, dashboard, visualization and reporting capabilities remain available
- Python **3.10–3.13** support declared in the package metadata
- GitHub Actions-based build/test/release workflow with PyPI Trusted Publishing/OIDC

## Install

### Core

```bash
python -m pip install tigerdatalab
```

### All data/analytics features

```bash
python -m pip install "tigerdatalab[all]"
```

### AI training-data preparation

The preparation layer does **not** require an LLM API key.

```bash
python -m pip install tigerdatalab
```

### Actual LLM fine-tuning

Install the optional training backend only when you want to train a model:

```bash
python -m pip install "tigerdatalab[train]"
```

## ⚡ Quick start

### Analyze a dataset

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

### Prepare AI training data

```python
from tigerdatalab.ai import AIDataset

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

dataset = AIDataset(rows, task="sft").run()

print(dataset.stats)
dataset.export("training_data")
```

The pipeline handles format preparation, validation, privacy protection, deduplication, quality scoring, deterministic splitting and JSONL export.

## 🤖 Fine-tune an LLM

TigerDataLab can orchestrate supervised fine-tuning of Hugging Face causal language models through the optional TRL backend.

```python
from tigerdatalab.ai import AIDataset, LLMTrainer

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

data = AIDataset(rows, task="sft").run()

trainer = LLMTrainer(
    model="Qwen/Qwen3-0.6B",
    output_dir="./my-tigerdatalab-model",
)

trainer.train_sft(data, epochs=1, batch_size=2, learning_rate=2e-5)
```

Or use the convenience API:

```python
from tigerdatalab.ai import train_sft

train_sft(
    "training_data/train.jsonl",
    model="Qwen/Qwen3-0.6B",
    output_dir="./my-model",
    epochs=1,
)
```

> Model training is performed by the libraries you explicitly install, including PyTorch, Transformers, Hugging Face Datasets and TRL. TigerDataLab provides the data-preparation and training-orchestration layer.

## 🧠 AI training-data workflow

```text
CSV / Excel / JSON / JSONL / application data
                    │
                    ▼
             TigerDataLab AI
                    │
                    ▼
       format + schema validation
                    │
                    ▼
          PII detection + masking
                    │
                    ▼
             deduplication
                    │
                    ▼
            quality scoring
                    │
                    ▼
       train / validation / test split
                    │
                    ▼
                 JSONL
                    │
                    ▼
       Hugging Face Datasets + TRL
                    │
                    ▼
             causal LM SFT
                    │
                    ▼
           saved fine-tuned model
```

## Supported AI dataset tasks

| Task | Purpose |
|---|---|
| `sft` | Supervised instruction fine-tuning |
| `chat` | Conversational/chat model datasets |
| `dpo` | Preference optimization datasets |
| `classification` | Labelled classification datasets |
| `text` | Generic text training datasets |

## Public API

### Analytics

```python
result = tdl.analyze("sales.xlsx")
result.summary()
result.kpis()
result.quality()
result.statistics()
result.trends()
result.customers()
result.products()
result.categories()
result.insights()
result.recommendations()
result.visualize()
result.growth()
result.anomalies()
result.ask()
result.dashboard("analysis/dashboard.html")
result.export("analysis")
result.report("analysis")
```

### AI

```python
from tigerdatalab.ai import (
    AIDataset,
    prepare,
    LLMTrainer,
    train_sft,
    validate_records,
    mask_record,
    deterministic_split_records,
)
```

## 📊 Large data

For larger datasets, use the DuckDB-backed interface:

```python
data = tdl.large("large_sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
data.query("SELECT category, AVG(revenue) FROM data GROUP BY category")
```

The large-data query layer refuses destructive SQL operations.

## 🔧 DataOps

```python
data = tdl.open("sales.xlsx")
data.update(where={"product_id": "SKU-1"}, values={"price": 499})
data.insert({"product_id": "SKU-99", "product": "Mouse", "price": 399})
data.delete(where={"product_id": "SKU-99"})
data.upsert({"product_id": "SKU-1", "price": 509}, key="product_id")
data.rollback()
data.save()
data.save_audit_log("analysis/audit.json")
```

Writes are controlled and audited. Zero-row updates/deletes raise explicit errors.

## 🖥️ CLI

```bash
tigerdatalab analyze sales.csv
tigerdatalab dashboard sales.csv -o analysis/dashboard.html
tigerdatalab profile sales.csv
tigerdatalab quality sales.csv
tigerdatalab clean sales.csv -o cleaned.xlsx
tigerdatalab report sales.csv -o analysis
```

## 🔐 Privacy and security

TigerDataLab is designed to be local-first:

- Datasets are not uploaded by the library.
- Analytics and training-data preparation do not require an external AI API.
- PII detection and masking run locally before training export.
- Dataset contents are not interpreted as arbitrary shell commands.
- The optional training backend uses only the model/data libraries you explicitly install.

Always review automatically detected PII and training data before using a dataset in production.

## 📦 Project layout

```text
tigerdatalab/
├── core.py
├── analytics/
├── quality/
├── insights/
├── visualization/
├── dashboard/
├── reporting/
├── dataops/
├── scale/
├── ai/
│   ├── datasets.py       # training-format adapters
│   ├── pipeline.py       # validation, privacy, dedup and export pipeline
│   ├── privacy.py        # local PII detection/masking
│   ├── quality.py        # dataset quality metrics
│   ├── schema.py         # training schema validation
│   └── training.py       # optional Hugging Face/TRL fine-tuning
└── cli/
```

## 🧪 Testing

Run the complete test suite with:

```bash
python -m pytest -v
```

The suite covers the analytics/DataOps/large-data platform and AI training-data functionality including validation, adapters, deterministic splitting, PII masking, deduplication and exports.

## 🛠️ Build and validate locally

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## 🚢 Release v3.0.7

Version **3.0.7** is the release target for the current package metadata. The repository is configured around GitHub Actions and PyPI Trusted Publishing/OIDC for release automation.

Recommended release flow:

```text
main
  │
  ├── tests
  ├── build package
  ├── validate metadata
  └── publish release → PyPI Trusted Publishing/OIDC
```

After the GitHub release workflow completes, verify the published package with:

```bash
python -m pip install --upgrade tigerdatalab
python -c "import tigerdatalab; print(tigerdatalab.__version__)"
```

## 📚 Links

- GitHub: https://github.com/abhi15724/tigerdatalab
- PyPI: https://pypi.org/project/tigerdatalab/

## License

MIT License.
