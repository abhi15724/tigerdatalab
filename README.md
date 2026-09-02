# TigerDataLab

**TigerDataLab is a production-ready, local-first data intelligence and model-agnostic AI application layer for companies.** It turns raw business data into trustworthy training data, knowledge, workflows, tools and evaluation pipelines around the AI/LLM a company already uses.

> **Don’t replace your AI. Teach it your business.**

TigerDataLab is designed to work across model families rather than lock a company to one vendor. It can prepare datasets for compatible open/self-hosted models, orchestrate supported fine-tuning APIs, add RAG and tools around hosted models, and provide a custom training adapter for proprietary or specialized training systems.

## v3.2.0 — Universal training architecture

The 3.2 release adds a model-agnostic training contract:

- `UniversalTrainer` provides one training API across model families.
- `TrainingBackend` is the stable adapter interface for any training system.
- Built-in Transformers + TRL backend supports compatible local/open causal LMs.
- `CallableTrainingBackend` lets vendors, proprietary models and custom trainers plug in without changing TigerDataLab's data pipeline.
- Training capabilities are explicitly declared instead of falsely claiming every model is directly trainable.
- Existing `LLMTrainer` and `train_sft()` APIs remain backward compatible.
- Training datasets remain provider-neutral and can be exported to standard JSONL formats.
- Existing RAG, tools, workflows, routing, registry, evaluation, analytics and DataOps APIs are preserved.

### What “any AI/LLM” means

There is no single training protocol shared by every AI model. A hosted proprietary model may expose only an API; an open model may expose downloadable weights; another model may require a vendor SDK or custom training service.

TigerDataLab solves this with adapters:

```text
                    TigerDataLab
                         │
              Universal Training API
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
 Transformers/TRL   Vendor training API   Custom backend
        │                │                 │
 Open/self-hosted     Hosted models      Any compatible
 model families       with tuning API    training system
```

So TigerDataLab is **model-agnostic**, but it does not pretend that unsupported vendors can be fine-tuned magically. If a model exposes no weight-training or fine-tuning interface, TigerDataLab can still improve its application using RAG, tools, workflows and evaluation.

## End-to-end AI architecture

```text
Company Data
    ↓
Clean + validate + protect PII
    ↓
AI training dataset
    ↓
┌───────────────┬──────────────┬───────────────┐
│ Fine-tuning   │ RAG          │ Tools/APIs    │
└───────────────┴──────────────┴───────────────┘
    ↓
Existing AI / LLM
    ↓
Business workflow
    ↓
Evaluation
    ↓
Company-specific AI application
```

## Install

```bash
python -m pip install tigerdatalab
```

For model training:

```bash
python -m pip install "tigerdatalab[train]"
```

## Prepare training data

```python
from tigerdatalab.ai import AIDataset

rows = [
    {"prompt": "What is revenue?", "response": "Revenue is income generated from sales."},
    {"prompt": "What is AOV?", "response": "AOV is average order value."},
]

data = AIDataset(rows, task="sft").run()
data.export("training_data")
```

TigerDataLab handles format conversion, schema validation, quality scoring, PII detection/masking, deduplication, deterministic splitting, lineage and JSONL export.

## Train a compatible open/self-hosted LLM

```python
from tigerdatalab.ai import UniversalTrainer

trainer = UniversalTrainer(
    model="Qwen/Qwen3-0.6B",
    output_dir="./my-model",
)
trainer.train_sft("training_data/train.jsonl", epochs=1)
```

The built-in backend uses PyTorch, Transformers, Hugging Face Datasets and TRL. It supports model families that those libraries can load and train with the selected task/configuration.

The old API remains valid:

```python
from tigerdatalab.ai import LLMTrainer

LLMTrainer("Qwen/Qwen3-0.6B", "./my-model").train_sft("training_data/train.jsonl")
```

## Plug in any custom training system

For a proprietary model, vendor SDK, internal training service, or another framework, implement the same normalized request contract:

```python
from tigerdatalab.ai import CallableTrainingBackend, UniversalTrainer


def train_with_my_system(request):
    # request.model
    # request.dataset
    # request.epochs / batch_size / learning_rate
    # request.options
    return my_vendor_or_internal_training_api(request)

backend = CallableTrainingBackend(train_with_my_system, name="my-provider")
trainer = UniversalTrainer("my-model", "./output", backend=backend)
trainer.train_sft("training_data/train.jsonl")
```

This keeps the TigerDataLab data/quality/privacy pipeline independent from the model vendor. New model families can be integrated without rewriting the dataset engine.

## Choose the right AI customization method

| Need | TigerDataLab path |
|---|---|
| Current company knowledge | RAG / knowledge base |
| Behavior, style, procedures, output format | Fine-tuning when supported |
| Perform real business actions | Tools / APIs |
| Multi-step business process | Workflows |
| Prove the model improved | Evaluation |
| Unsupported vendor training API | Custom `TrainingBackend` |

TigerDataLab does **not** claim that a proprietary hosted model can be retrained when its provider does not expose such a capability.

## Build a company AI application

```python
from tigerdatalab.ai import CompanyAI, KnowledgeBase, ModelRouter, OpenAIProvider

provider = OpenAIProvider()  # reads OPENAI_API_KEY from the environment
router = ModelRouter().add(provider, "your-model")

kb = KnowledgeBase()
kb.add("returns", "Customers can return unused products within 30 days.")

ai = CompanyAI(router, knowledge_base=kb)
result = ai.ask("What is the return policy?")
print(result.output)
```

No API key is stored in datasets, lineage or registry metadata.

## RAG / knowledge base

```python
from tigerdatalab.ai import KnowledgeBase

kb = KnowledgeBase()
kb.add("policy", "Refunds are issued within 7 business days.", department="finance")
kb.add("support", "Priority customers receive 24/7 support.", department="support")

print(kb.search("refund timing", top_k=3))
print(kb.context("refund timing"))
```

The core RAG implementation is dependency-light. Production deployments can place an embedding/vector database behind the same application boundary.

## Safe tools / function calling

```python
from tigerdatalab.ai import Tool, ToolRegistry

registry = ToolRegistry()
registry.register(Tool(
    name="get_order",
    description="Get an order by ID",
    function=lambda order_id: {"id": order_id, "status": "shipped"},
    parameters={
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
))

print(registry.schemas())
print(registry.execute("get_order", {"order_id": "ORD-1001"}))
```

Only explicitly registered tools can execute. Model output is never treated as arbitrary Python or shell code.

## Business workflows

```python
from tigerdatalab.ai import Workflow, WorkflowStep

workflow = Workflow("order-support")
workflow.add_step(WorkflowStep("load", lambda s: {"order": {"status": "delayed"}}))
workflow.add_step(WorkflowStep("decision", lambda s: "escalate" if s["order"]["status"] == "delayed" else "resolve", output_key="decision"))

result = workflow.run({"order_id": "ORD-1001"})
print(result.status, result.state)
```

## Model routing

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider

router = ModelRouter()
router.add(OpenAIProvider(), "primary-model")
router.add(OpenAIProvider(), "fallback-model")

response = router.chat([{"role": "user", "content": "Summarize this order."}])
```

## Evaluation

```python
from tigerdatalab.ai import evaluate

result = evaluate(lambda messages: "4", [{"prompt": "2+2?", "expected": "4"}])
print(result.score, result.average_latency_ms)
```

Use representative test sets and task-specific scorers for production evaluation.

## Analytics platform

All existing analytics capabilities remain available:

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

## Architecture

```text
                    TigerDataLab
┌──────────────────────────────────────────────────────┐
│ Analytics │ Data Quality │ DataOps │ Dashboards      │
├──────────────────────────────────────────────────────┤
│ Training Data │ PII │ Lineage │ Universal Trainer   │
├──────────────────────────────────────────────────────┤
│ RAG │ Providers │ Tools │ Workflows │ Router        │
├──────────────────────────────────────────────────────┤
│ Registry │ Evaluation │ CompanyAI │ Backends        │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
             Any supported AI training system
                         │
                         ▼
                  Company AI application
```

## Security principles

- Local-first data processing by default.
- No mandatory LLM API for dataset preparation.
- API credentials remain outside training datasets and metadata.
- PII scanning/masking happens locally in the training-data pipeline.
- Tool execution is explicit and allow-listed.
- Training backends are explicit adapters; unsupported capabilities fail clearly.
- Training data and model outputs should be reviewed before production use.

## Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

## Release

The package version is **3.2.0**. The repository's GitHub Actions release workflow uses PyPI Trusted Publishing/OIDC after a published GitHub Release.

## Project layout

```text
tigerdatalab/
├── analytics/ quality/ insights/ visualization/
├── dashboard/ reporting/ dataops/ scale/
├── ai/
│   ├── datasets.py
│   ├── pipeline.py
│   ├── privacy.py
│   ├── quality.py
│   ├── schema.py
│   ├── training.py
│   ├── providers.py
│   ├── rag.py
│   ├── evaluation.py
│   ├── tools.py
│   ├── workflows.py
│   ├── router.py
│   ├── registry.py
│   └── system.py
└── cli/
```

## License

MIT License.
