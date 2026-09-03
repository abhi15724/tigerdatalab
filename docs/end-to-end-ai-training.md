# End-to-end AI/LLM training with TigerDataLab

TigerDataLab now provides a single project API for the complete training lifecycle:

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

The library prepares and governs the data lifecycle. Actual model-weight updates are performed by a compatible training backend. The built-in backend uses Hugging Face Transformers + Datasets + TRL and supports optional PEFT/LoRA. Custom backends can be supplied for other training systems.

## 1. Install

```bash
python -m pip install "tigerdatalab[train]"
```

## 2. Example source data

Create `company_support.csv`:

```csv
question,answer,department
"How do I reset my password?","Open Settings, choose Security, and select Reset Password.",support
"What is the return policy?","Unused products may be returned within 30 days.",support
"How do I process an invoice?","Follow the approved AP workflow before payment.",finance
```

## 3. One project for the complete lifecycle

```python
import tigerdatalab as td

project = td.create_project("company-support")

ai = project.ai_training(
    "support-model",
    source="company_support.csv",
    task="sft",
    output_dir="./support-ai-run",
)

# 1. Clean: PII masking, format conversion, deduplication and basic filtering
ai.clean_data()

# 2. Validate the prepared records
validation = ai.validate_data()
print(validation)

# 3. Explicitly choose SFT format
ai.convert_to_sft()

# 4. Stable 80/10/10 train/validation/test split
splits = ai.split_dataset(
    train_ratio=0.8,
    validation_ratio=0.1,
    strategy="hash",
)
print({name: len(records) for name, records in splits.items()})

# 5. Fine-tune a compatible open model
trainer = ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="lora",
    epochs=2,
    batch_size=2,
    learning_rate=1e-4,
)

# 6. Evaluate a callable model against a test set.
# The callable can wrap your local fine-tuned model, an API endpoint,
# OpenRouter, or another inference service.
def my_model(prompt: str) -> str:
    # Replace with your actual inference implementation.
    return "your model response"

result = ai.evaluate_model(my_model)
print(result.score)

# 7. Save a machine-readable run manifest
print(ai.export_run_manifest())
```

## 4. What each stage produces

### `clean_data()`

Uses TigerDataLab's existing AI dataset pipeline. It masks detected PII, converts records into the selected training format, removes duplicates, applies length filters and validates records.

### `validate_data()`

Returns TigerDataLab's structured `ValidationReport`. Invalid examples are removed by the preparation pipeline and the validation statistics are recorded in the dataset metadata.

### `convert_to_sft()`

Selects the SFT adapter and produces examples compatible with conversational SFT workflows, such as:

```json
{"messages":[{"role":"user","content":"What is the return policy?"},{"role":"assistant","content":"Unused products may be returned within 30 days."}]}
```

### `split_dataset()`

Creates `train`, `validation`, and `test` records. The default hash strategy is deterministic, which makes repeated runs stable for the same prepared records and ratios.

### `train_model()`

Uses the selected training backend. With `backend="auto"`, a Hugging Face/Transformers model ID or local model path is sent to the built-in SFT backend.

For LoRA:

```python
ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="lora",
    lora_r=16,
    lora_alpha=32,
    lora_dropout=0.05,
)
```

For QLoRA-style 4-bit loading:

```python
ai.train_model(
    model="Qwen/Qwen3-0.6B",
    method="qlora",
)
```

QLoRA/4-bit training also requires a compatible Transformers/bitsandbytes/hardware setup; TigerDataLab does not guarantee that every model supports quantized training.

### `evaluate_model()`

Runs TigerDataLab's evaluation suite against a callable. The default scorer can compare a returned answer with an `expected` value; a custom scorer can implement domain-specific quality rules.

```python
from tigerdatalab.ai import evaluate

result = evaluate(
    my_model,
    [
        {
            "prompt": "What is the return policy?",
            "expected": "Unused products may be returned within 30 days.",
        }
    ],
)

print(result.score)
print(result.average_latency_ms)
```

## 5. Output artifacts

With `output_dir="./support-ai-run"`, the dataset stage produces artifacts such as:

```text
support-ai-run/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
├── dataset_card.md
├── evaluation_report.json       # after evaluate_model()
├── run_manifest.json            # after export_run_manifest()
└── model/                       # default training output
    ├── adapter_model.safetensors   # LoRA runs, when supported
    ├── adapter_config.json
    └── tokenizer files
```

A full-model run can contain model weight files instead of an adapter. The exact files depend on the selected model and backend.

## 6. OpenRouter is optional

OpenRouter is an **inference/API provider**, not the mechanism that modifies local model weights. You can use an OpenRouter-compatible provider to generate, enrich or judge data, and you can use OpenRouter to evaluate a trained model through an API wrapper.

Example inference wrapper:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def openrouter_model(prompt: str) -> str:
    response = client.chat.completions.create(
        model="YOUR_OPENROUTER_MODEL",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""

result = ai.evaluate_model(openrouter_model)
```

The model slug and availability depend on OpenRouter's current catalog. Do not hard-code a model described as free unless you have verified its current availability and terms.

## 7. Other training backends

TigerDataLab is not locked to one vendor. The training contract accepts a `TrainingBackend` instance or a callable backend, so teams can integrate proprietary training APIs or other model-training systems.

```python
from tigerdatalab.ai import CallableTrainingBackend, TrainingCapabilities

def enterprise_train(request):
    # Call your organization's training platform here.
    print(request.model, request.output_dir, request.task)
    return {"status": "submitted"}

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

This adapter architecture means TigerDataLab can prepare one governed dataset while different customers use different model-training infrastructure.

## 8. Production pattern for a company

```text
Approved company data
        ↓
TigerDataLab ingestion
        ↓
PII masking + data quality
        ↓
Deduplication + validation
        ↓
SFT / preference / evaluation format
        ↓
Deterministic dataset split
        ↓
Training backend (TRL / custom)
        ↓
Company model or adapter
        ↓
TigerDataLab evaluation
        ↓
Quality + latency + failure report
        ↓
Registry / deployment pipeline
```

For sensitive enterprise data, add customer-controlled storage, access controls, retention/deletion policies, audit logging, encryption, legal data-processing agreements and an appropriate deployment model before production use.

## Scope

TigerDataLab does **not** claim to train literally every AI model. Model architectures, licenses, tokenizers, hardware requirements and training APIs differ. The universal layer means the **data/training contract is stable**, while compatible model-training backends can be swapped in without redesigning the data pipeline.
