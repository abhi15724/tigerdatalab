# TigerDataLab — हिंदी

**TigerDataLab एक unified Data + AI engineering platform है जो Data Analytics, Data Science, Data Engineering, AI Training और Company AI workflow training को एक साथ जोड़ता है।**

> **अपने AI को बदलें नहीं। उसे अपना data, अपने rules और अपना workflow सिखाएँ।**

## मुख्य उपयोग

| भूमिका | TigerDataLab का उपयोग |
|---|---|
| Data Analyst | KPI, trends, quality, insights, dashboards और reports |
| Data Scientist | profiling, reproducible train/test split, correlation और ML-ready data |
| Data Engineer | deterministic ETL, cleaning, transformation और pipeline manifests |
| AI/ML Engineer | SFT, DPO, classification, PII masking, deduplication, validation और JSONL datasets |
| Company AI Builder | company knowledge, RAG, rules, workflows, approved tools/APIs और evaluation |

## Installation

```bash
python -m pip install tigerdatalab
```

Training capabilities के लिए:

```bash
python -m pip install "tigerdatalab[train]"
```

## Quick Start

```python
from tigerdatalab import create_project

tdl = create_project("my-company")
result = tdl.analyze("sales.xlsx")
print(result.summary())
```

## Data Analyst

```python
result = tdl.analyze("sales.xlsx")
print(result.kpis())
print(result.quality())
print(result.insights())
```

आप sales, finance, customer और operational data से KPIs, trends, business insights तथा reports बना सकते हैं।

## Data Scientist

```python
frame = tdl.load("customers.csv")
profile = tdl.profile(frame)
train, test = tdl.data_science.train_test_split(frame, test_size=0.2, seed=42)
correlation = tdl.data_science.correlation(train)
```

TigerDataLab data exploration और preparation layer देता है; आप output को अपने ML framework में उपयोग कर सकते हैं।

## Data Engineer

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

इससे reproducible और testable transformations बनाए जा सकते हैं।

## AI Training

TigerDataLab raw examples को high-quality AI training datasets में बदलता है:

```text
Raw Data → Format → PII Mask → Deduplicate → Validate → Quality → Split → JSONL → Training Backend
```

Supported task styles:

- SFT — supervised instruction/chat
- DPO — preferred/rejected responses
- Classification — text + label
- Instruction — instruction/input/output
- Text — general text training

Example:

```python
project = tdl.ai_training("support-model", task="sft")
dataset = project.prepare("support_examples.csv", "training_data")
print(dataset.summary())
```

## Company AI और Workflow Training

Company AI में केवल prompt काफी नहीं होता। सामान्यतः चार layers चाहिए:

```text
Knowledge → Behavior → Workflow → Tools
```

उदाहरण: customer return process:

```text
Customer Request
      ↓
Identify Customer
      ↓
Retrieve Order
      ↓
Check Policy
      ↓
Check Eligibility
      ↓
Business Rules
      ↓
Create Return / Explain Reason
      ↓
Escalate High-Risk Cases
      ↓
Final Response
```

LLM workflow का एक component है; business workflow को explicit और controllable रखना चाहिए।

## RAG

बार-बार बदलने वाली company information के लिए RAG उपयोग करें:

```python
from tigerdatalab.ai import Document, KnowledgeBase

kb = KnowledgeBase()
kb.add(Document(
    "returns-policy",
    "Unused products can be returned within 30 days.",
    {"department": "support"},
))

print(kb.context("return policy", top_k=3))
```

## Fine-Tuning बनाम RAG

| आवश्यकता | तरीका |
|---|---|
| बदलती company information | RAG |
| Policies/documents | RAG |
| Stable response behavior | Fine-tuning |
| Output format | Fine-tuning / prompt / schema |
| Multi-step business process | Workflow |
| Business system में action | Approved tools/APIs |
| Quality measurement | Evaluation |

## Model Providers

TigerDataLab provider adapters के माध्यम से OpenAI, Anthropic, Gemini, Groq, OpenRouter, Mistral, Together AI और OpenAI-compatible endpoints के साथ काम कर सकता है।

## सुरक्षा

- API keys को source code या datasets में store न करें।
- Environment variables या secrets manager का उपयोग करें।
- Tools को allow-list करें।
- Sensitive/high-risk workflows में human approval रखें।
- Dataset lineage और evaluation evidence बनाए रखें।

## महत्वपूर्ण सीमा

TigerDataLab यह दावा नहीं करता कि हर proprietary hosted LLM के weights को सीधे modify किया जा सकता है। Fine-tuning तभी संभव है जब संबंधित provider/model compatible training capability देता हो। अन्य models के लिए RAG, workflows, tools, routing और evaluation का उपयोग किया जा सकता है।

## पूरी documentation

English documentation के लिए [README.md](README.md) देखें।
