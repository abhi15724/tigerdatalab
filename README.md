# TigerDataLab

**TigerDataLab** is an automated **Data Analytics + Data Quality + Visualization + Business Intelligence + DataOps + AI Training Data + LLM Fine-Tuning** platform built on pandas, NumPy, DuckDB and Plotly. It complements these libraries rather than replacing them.

> **Analyze. Clean. Understand. Prepare. Fine-tune.**

## Install

```bash
pip install tigerdatalab

# Large data, PDF and AI/LLM training features
pip install "tigerdatalab[all]"
```

For only LLM fine-tuning:

```bash
pip install "tigerdatalab[train]"
```

## Analytics quick start

```python
import tigerdatalab as tdl

result = tdl.analyze("sales.xlsx")
print(result.summary())
result.report("analysis")
```

For large data:

```python
data = tdl.large("sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue", "SUM(profit) AS profit")
```

## AI training-data pipeline

TigerDataLab prepares raw data for machine learning and LLM fine-tuning locally.

Supported workflows include:

- SFT / instruction tuning
- Chat / conversational datasets
- DPO / preference datasets
- Classification datasets
- Text datasets
- Schema validation
- PII detection and deterministic masking
- Duplicate detection and removal
- Quality scoring
- Train/validation/test splitting
- Dataset lineage and dataset cards
- JSONL export

```python
from tigerdatalab.ai import AIDataset

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

dataset = AIDataset(rows, "sft").run()
print(dataset.stats)
dataset.export("training_data")
```

The preparation layer does not require an LLM API key.

## Fine-tune an LLM with TigerDataLab

TigerDataLab can now drive supervised fine-tuning of Hugging Face causal language models through an optional TRL backend. The core package remains lightweight; install the `train` extra only when you want actual model training.

```python
from tigerdatalab.ai import AIDataset, LLMTrainer

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

# 1. Clean, validate, mask PII and deduplicate
data = AIDataset(rows, task="sft").run()

# 2. Fine-tune a causal language model
trainer = LLMTrainer(
    model="Qwen/Qwen3-0.6B",
    output_dir="./my-tigerdatalab-model",
)
trainer.train_sft(
    data,
    epochs=1,
    batch_size=2,
    learning_rate=2e-5,
)
```

Or use the one-line convenience API:

```python
from tigerdatalab.ai import train_sft

train_sft(
    "training_data/train.jsonl",
    model="Qwen/Qwen3-0.6B",
    output_dir="./my-model",
    epochs=1,
)
```

### What happens

```text
CSV / Excel / JSON / JSONL / application data
                    ↓
             TigerDataLab AI
                    ↓
        format + validation + PII mask
                    ↓
             deduplication
                    ↓
          quality + lineage report
                    ↓
          train / validation / test
                    ↓
                JSONL
                    ↓
       Hugging Face Datasets + TRL
                    ↓
             causal LM SFT
                    ↓
             saved fine-tuned model
```

TigerDataLab is the **data preparation and training orchestration layer**. PyTorch, Transformers, Datasets and TRL perform the underlying model training when the `train` extra is installed.

## Public API

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

AI APIs:

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

## DataOps

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

Writes are controlled and audited; zero-row updates/deletes raise explicit errors.

## Large data

```python
data = tdl.large("large_sales.parquet")
data.count()
data.aggregate("category", "SUM(revenue) AS revenue")
data.query("SELECT category, AVG(revenue) FROM data GROUP BY category")
```

Destructive SQL is refused by the large-data query layer.

## CLI

```bash
tigerdatalab analyze sales.csv
tigerdatalab dashboard sales.csv -o analysis/dashboard.html
tigerdatalab profile sales.csv
tigerdatalab quality sales.csv
tigerdatalab clean sales.csv -o cleaned.xlsx
tigerdatalab report sales.csv -o analysis
```

## Privacy and security

TigerDataLab is local-first:

- Datasets are not uploaded by the library.
- No external AI API is required by the analytics or data-preparation layers.
- PII masking happens locally before training export.
- Arbitrary shell commands are not executed from dataset contents.
- The optional training backend uses the model/data libraries you explicitly install.

## Project layout

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

## Testing

```bash
python -m pytest -v
```

The test suite covers the existing analytics/DataOps/large-data platform plus AI training-data validation, adapters, deterministic splitting, PII masking, deduplication and exports.

## PyPI publishing

Releases are tested and built by GitHub Actions and published to PyPI using PyPI Trusted Publishing/OIDC.

```text
GitHub Release → Tests → Build → Metadata validation → PyPI Trusted Publishing
```

Local package validation:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

## Version

**3.0.7**

- GitHub: https://github.com/abhi15724/tigerdatalab
- PyPI: https://pypi.org/project/tigerdatalab/

## License

MIT License.
