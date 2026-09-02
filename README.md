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

## 📦 Installation

```bash
python -m pip install tigerdatalab==4.0.0
```

Or install the latest PyPI release:

```bash
python -m pip install tigerdatalab
```

AI training extras:

```bash
python -m pip install "tigerdatalab[train]==4.0.0"
```

Full optional capabilities:

```bash
python -m pip install "tigerdatalab[all]==4.0.0"
```

> **Release:** TigerDataLab **v4.0.0** is the current development release for the unified Data + AI platform. The PyPI version badge above always reflects the version currently published on PyPI.

---

## ⚡ Quick Start

```python
from tigerdatalab import create_project

tdl = create_project("my-company")
result = tdl.analyze("sales.xlsx")
print(result.summary())
print(result.kpis())
```

---

## 🤖 AI Training

TigerDataLab provides the AI data and training layer between raw data and a compatible training system.

```text
Raw Examples → Format → PII → Deduplicate → Validate → Quality
                                                        ↓
                                               Train / Val / Test
                                                        ↓
                                                  JSONL Export
                                                        ↓
                                               Training Backend
```

Supported dataset styles include **SFT, DPO, Classification, Instruction and Text**. Training adapters support compatible open/self-hosted models and other backends where a supported SDK/API/adapter exists.

---

## 🏢 Company AI

Company AI combines current knowledge, stable behavior, controlled workflows, approved tools/APIs and evaluation.

```text
Company Data → Trusted Data → Knowledge / RAG
                              ↓
                    Rules + Workflow + Tools
                              ↓
                     Model Router / AI Layer
                              ↓
                         Evaluation
                              ↓
                     Production Company AI
```

---

## 🔀 Intelligent Multi-Provider Model Routing

TigerDataLab is **not limited to OpenAI**. `ModelRouter` can combine any registered provider, including OpenAI, Anthropic, Google Gemini, Groq, Mistral, OpenRouter, Together AI, and custom `Provider` implementations.

### Simple fallback — backward compatible

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider, AnthropicProvider

router = ModelRouter()
router.add(OpenAIProvider(), "gpt-5")
router.add(AnthropicProvider(), "claude-sonnet")

answer = router.chat([
    {"role": "user", "content": "Summarize this customer issue."}
])
```

### Cost-aware routing

```python
from tigerdatalab.ai import ModelRouter, OpenAIProvider, GroqProvider

router = ModelRouter(strategy="cost")
router.add(OpenAIProvider(), "gpt-5-mini", estimated_cost_per_1k_tokens=0.40)
router.add(GroqProvider(), "llama-model", estimated_cost_per_1k_tokens=0.08)
answer = router.chat(messages)
```

### Latency-aware routing

```python
router = ModelRouter(strategy="latency")
router.add(provider_a, "fast-model", estimated_latency_ms=150)
router.add(provider_b, "slow-model", estimated_latency_ms=900)
```

### Capability-aware routing

```python
router = ModelRouter(strategy="balanced")
router.add(text_model, "text-model", capabilities=("chat",))
router.add(vision_model, "vision-model", capabilities=("chat", "vision"))
answer = router.chat(messages, required_capabilities={"vision"})
```

### Health-aware fallback

The router tracks success/failure counts and observed latency, temporarily removes repeatedly failing targets through a cooldown, and falls back to another eligible provider. Use `router.health()` for non-secret telemetry.

Available strategies:

| Strategy | Behavior |
|---|---|
| `ordered` | Original first-success/fallback behavior |
| `cost` | Prefer lowest configured model cost |
| `latency` | Prefer lowest configured latency |
| `balanced` | Combine configured cost, latency and observed reliability |

Cost and latency estimates are user-supplied routing metadata; TigerDataLab does not claim live provider pricing or latency.

---

## 🔎 RAG, Workflows and Tools

Use **RAG** for changing company knowledge, **fine-tuning** for stable behavior, **workflows** for controlled multi-step processes, and **allow-listed tools/APIs** for business actions.

The LLM is a component inside the workflow — not the workflow itself.

---

## 📈 Evaluation

Evaluate accuracy, policy compliance, hallucination rate, workflow compliance, tool success, latency and model/version regressions before production.

---

## 🔐 Security

- Keep API keys outside source code and datasets.
- Use environment variables or a secrets manager.
- Allow-list tools and business actions.
- Use human approval for high-risk decisions.
- Keep dataset lineage and evaluation evidence.
- Never treat arbitrary model output as executable Python or shell code.

---

## 🌐 Supported Model Providers

TigerDataLab includes adapters for **OpenAI, Anthropic, Google Gemini, Groq, OpenRouter, Mistral, Together AI, and OpenAI-compatible endpoints**.

You can also implement your own provider by subclassing `Provider`.

---

## 🧪 Testing

```bash
python -m pip install -e ".[all,dev]"
python -m pytest -v
```

---

## 🌍 Read TigerDataLab in Your Language

- 🇬🇧 **English:** `README.md`
- 🇮🇳 **हिंदी:** `README.hi.md`

---

## 🏗️ End-to-End Architecture

```text
Company Data
    ↓
Data Engineering → Data Quality → Analytics / Data Science
    ↓
Trusted AI Data → AI Dataset Builder → Training / RAG
    ↓
Company Knowledge + Rules + Workflow + Tools
    ↓
Intelligent Model Router
    ↓
OpenAI / Claude / Gemini / Groq / Mistral / OpenRouter / Together / Custom
    ↓
Evaluation + Monitoring
    ↓
Production AI
```

---

## 📄 License

See `LICENSE` for the project license.
