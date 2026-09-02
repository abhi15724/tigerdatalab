<div align="center">

# 🐯 TigerDataLab

### **From Raw Data to Production AI**

**A unified Python platform for Data Analytics, Data Science, Data Engineering, AI training data, RAG, Company AI agents, tools, workflows, and evaluation.**

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

<p>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/v/tigerdatalab.svg?style=for-the-badge&logo=pypi&logoColor=white&cacheSeconds=0&v=4.1.0" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tigerdatalab/"><img src="https://img.shields.io/pypi/pyversions/tigerdatalab?style=for-the-badge&logo=python&logoColor=white" alt="Python versions"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/abhi15724/tigerdatalab/ci.yml?style=for-the-badge&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/abhi15724/tigerdatalab/blob/main/LICENSE"><img src="https://img.shields.io/github/license/abhi15724/tigerdatalab?style=for-the-badge" alt="License"></a>
</p>

**v4.1.0 • Python 3.10–3.13**

</div>

---

# Table of Contents

- [What is TigerDataLab?](#what-is-tigerdatalab)
- [Who can use it?](#who-can-use-it)
- [Installation](#installation)
- [The complete data-to-AI lifecycle](#the-complete-data-to-ai-lifecycle)
- [1. Data Analyst](#1-data-analyst)
- [2. Data Quality](#2-data-quality)
- [3. Data Cleaning](#3-data-cleaning)
- [4. Data Scientist](#4-data-scientist)
- [5. Data Engineer](#5-data-engineer)
- [6. AI training-data preparation](#6-ai-training-data-preparation)
- [7. AI model training](#7-ai-model-training)
- [8. Company AI / RAG](#8-company-ai--rag)
- [9. Company AI Agent](#9-company-ai-agent)
- [10. AI tools](#10-ai-tools)
- [11. Business workflows](#11-business-workflows)
- [12. Model routing](#12-model-routing)
- [13. Evaluation](#13-evaluation)
- [14. End-to-end Company AI example](#14-end-to-end-company-ai-example)
- [15. Output files and artifacts](#15-output-files-and-artifacts)
- [16. Supported inputs](#16-supported-inputs)
- [17. Production architecture](#17-production-architecture)
- [18. Security and safety](#18-security-and-safety)
- [19. Project structure](#19-project-structure)
- [20. Important scope and limitations](#20-important-scope-and-limitations)
- [21. API quick reference](#21-api-quick-reference)

---

# What is TigerDataLab?

TigerDataLab is a Python platform for moving from **raw business data to trusted data and then to production-oriented AI applications**.

It brings together:

```text
Raw Data
   ↓
Load / Ingest
   ↓
Profile + Quality Checks
   ↓
Clean + Transform
   ↓
Analytics / Data Science
   ↓
Trusted Data
   ↓
AI Dataset Preparation
   ↓
┌───────────────────────────────┐
│ General AI Training           │
│ Company AI / RAG              │
│ Company AI Agents             │
└───────────────────────────────┘
   ↓
Tools + Workflows
   ↓
Evaluation
   ↓
Application Integration
```

The goal is not to replace every existing analytics, ML, database, or LLM platform. Instead, TigerDataLab provides a common data and AI engineering layer that can be used with the tools and model providers a team already uses.

---

# Who can use it?

| Role | What TigerDataLab can help with |
|---|---|
| 📊 Data Analyst | Load, profile, clean, analyze and understand datasets |
| 🧪 Data Scientist | Profiling, correlation, train/test preparation and ML data workflows |
| ⚙️ Data Engineer | Deterministic transformations and pipeline manifests |
| 🤖 AI / LLM Engineer | Training-data preparation, dataset quality, lineage and compatible model training |
| 🏢 AI / Automation Team | Company knowledge, RAG, tools, workflows and evaluation |
| 💼 Business Team | Turn operational data and policies into AI-ready application inputs |

---

# Installation

## Basic installation

```bash
python -m pip install tigerdatalab
```

Verify the installation:

```python
import tigerdatalab as td

print(td.__version__)
```

Expected form:

```text
4.1.0
```

## Training installation

If you want to use the built-in Transformers-based training backend:

```bash
python -m pip install "tigerdatalab[train]"
```

Training dependencies include the ecosystem required by the built-in backend, such as Transformers, Datasets and TRL.

> Training dependency versions can change independently from TigerDataLab. For production environments, pin and test the versions used by your organization.

---

# The complete data-to-AI lifecycle

A typical project can look like this:

```text
                 COMPANY / RAW DATA
                         ↓
                 1. DATA INGESTION
                         ↓
                 2. DATA PROFILING
                         ↓
                 3. DATA QUALITY
                         ↓
                 4. DATA CLEANING
                         ↓
                 5. DATA ENGINEERING
                         ↓
              TRUSTED BUSINESS DATA
                         ↓
          ┌──────────────┴──────────────┐
          ↓                             ↓
   DATA ANALYTICS                 DATA SCIENCE
          ↓                             ↓
          └──────────────┬──────────────┘
                         ↓
                 AI DATASET BUILDER
                         ↓
          ┌──────────────┴──────────────┐
          ↓                             ↓
    GENERAL AI TRAINING          COMPANY AI
                                        ↓
                                  RAG + TOOLS
                                        ↓
                                   WORKFLOWS
                                        ↓
                                   EVALUATION
                                        ↓
                              AI APPLICATION
```

---

# 1. Data Analyst

TigerDataLab can be used as the first layer of a data-analysis workflow.

## 1.1 Load a CSV

Example file `sales.csv`:

```csv
order_id,customer,region,product,quantity,revenue
1001,Acme,North,Laptop,2,120000
1002,Globex,West,Monitor,5,75000
1003,Acme,North,Keyboard,10,25000
1004,Initech,South,Laptop,1,60000
1005,Globex,West,Mouse,20,30000
```

Python:

```python
import tigerdatalab as td

tiger = td.create_project("SalesAnalysis")

df = tiger.load("sales.csv")

print(df.head())
```

Output is a DataFrame containing the loaded business data:

```text
   order_id customer region   product  quantity  revenue
0      1001     Acme  North     Laptop         2   120000
1      1002   Globex   West    Monitor         5    75000
2      1003     Acme  North   Keyboard        10    25000
3      1004  Initech  South     Laptop         1    60000
4      1005   Globex   West      Mouse        20    30000
```

## 1.2 Profile the dataset

```python
profile = tiger.profile(df)
print(profile)
```

The profile is a structured `DatasetProfile` object. It is intended to describe dataset-level information such as:

- row and column counts
- column names
- data types
- missing-value information
- numeric/categorical characteristics
- quality-oriented metadata

Example conceptual output:

```text
DatasetProfile(
    rows=5,
    columns=6,
    columns=[
        "order_id",
        "customer",
        "region",
        "product",
        "quantity",
        "revenue"
    ]
)
```

The exact representation depends on the object's implementation and Python version.

## 1.3 Run analysis

```python
result = tiger.analyze("sales.csv")
print(result)
```

`analyze()` returns an `AnalysisResult` containing the analysis result rather than writing an arbitrary text file by default.

Use it when you want a programmatic analysis object that can be inspected by your application.

Example usage:

```python
print(result.summary)
```

> The exact fields available on `AnalysisResult` should be checked against the installed version when writing application code. The important contract is that the analysis is returned as a structured result object rather than requiring you to parse terminal text.

---

# 2. Data Quality

Data quality is important before analytics, ML or AI training.

## 2.1 Quality check a dataset

```python
import tigerdatalab as td

result = td.quality_check("sales.csv")
print(result)
```

The quality layer is designed to identify common problems such as:

```text
Missing values
      ↓
Duplicates
      ↓
Invalid / inconsistent values
      ↓
Type problems
      ↓
Quality failures
```

Example conceptual report:

```text
Data Quality Report
-------------------
Rows: 5
Columns: 6
Missing values: 0
Duplicate rows: 0
Status: PASS
```

For real datasets, the report values depend entirely on the input data.

## 2.2 Why run quality checks first?

For example, an AI support dataset may contain:

```text
customer_email = "abc@gmail.com"
customer_email = "abc@gmail.com"
customer_email = "ABC@gmail.com"
customer_email = ""
```

If those records are used directly for training, the model may learn duplicated or inconsistent examples.

Quality processing should happen before training-data generation.

---

# 3. Data Cleaning

TigerDataLab also exposes file-level cleaning helpers.

## 3.1 Clean a file

```python
import tigerdatalab as td

output = td.clean_file(
    "raw_customers.xlsx",
    output_path="clean_customers.xlsx",
)

print(output)
```

The cleaning operation is intended to produce a cleaned file artifact.

Example workflow:

```text
raw_customers.xlsx
        ↓
Read workbook
        ↓
Detect data-quality problems
        ↓
Clean / normalize
        ↓
Write cleaned workbook
        ↓
clean_customers.xlsx
```

The output is a file path/result representing the generated cleaned artifact, depending on the installed API version.

> Always validate business-specific cleaning rules. Automatic cleaning should not silently change business meaning.

---

# 4. Data Scientist

TigerDataLab provides lightweight data-science helpers without forcing a particular ML framework.

## 4.1 Create a project

```python
import tigerdatalab as td

tiger = td.create_project("CustomerPrediction")
df = tiger.load("customers.csv")
```

## 4.2 Profile for ML preparation

```python
profile = tiger.data_science.profile(df)
print(profile)
```

This provides structured profiling information that can be used before feature engineering and model development.

## 4.3 Correlation analysis

```python
correlation = tiger.data_science.correlation(df)
print(correlation)
```

For a dataset such as:

```text
age,income,orders,customer_value
25,30000,2,5000
31,55000,7,22000
42,90000,15,70000
```

The correlation output is a numeric correlation structure that can be consumed by Python code.

Conceptually:

```text
                 age  income  orders  customer_value
age             1.00    0.91    0.82            0.84
income          0.91    1.00    0.89            0.94
orders          0.82    0.89    1.00            0.96
customer_value  0.84    0.94    0.96            1.00
```

Exact values depend on the data.

## 4.4 Reproducible train/test split

```python
train, test = tiger.data_science.train_test_split(
    df,
    test_size=0.2,
    seed=42,
)

print("Train:", train.shape)
print("Test:", test.shape)
```

Example output:

```text
Train: (800, 12)
Test: (200, 12)
```

The exact row counts depend on the input dataset.

The `seed=42` makes the split deterministic for reproducible experiments.

## 4.5 Continue with your ML framework

TigerDataLab does not require you to abandon your preferred ML framework.

```text
TigerDataLab
     ↓
Data preparation
     ↓
Your ML framework
     ↓
Model training
     ↓
Evaluation
```

---

# 5. Data Engineer

Use `DataPipeline` for ordered, deterministic transformations.

## 5.1 Build an ETL pipeline

```python
import tigerdatalab as td

tiger = td.create_project("CustomerETL")
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

print(clean_df.head())
```

## 5.2 What happens?

```text
raw_customers.csv
       ↓
remove_duplicates
       ↓
remove_missing_ids
       ↓
normalize_email
       ↓
clean_df
```

Every pipeline step is executed in the configured order and must return a DataFrame.

## 5.3 Example input

```text
customer_id,email
101, ALICE@EXAMPLE.COM
101, ALICE@EXAMPLE.COM
102, bob@example.com
,missing@example.com
```

After the example transformations, the expected business shape is approximately:

```text
customer_id,email
101,alice@example.com
102,bob@example.com
```

The exact output depends on the transformations you register.

## 5.4 Save a pipeline manifest

```python
pipeline.save_manifest("pipeline_manifest.json")
```

Example artifact:

```json
{
  "steps": [
    {"name": "remove_duplicates"},
    {"name": "remove_missing_ids"},
    {"name": "normalize_email"}
  ]
}
```

The manifest is useful for reproducibility and auditing the configured transformation sequence.

---

# 6. AI Training-Data Preparation

This is one of the most important parts of TigerDataLab.

TigerDataLab can transform raw training-oriented source data into a structured AI dataset with train/validation/test splits and supporting metadata.

## 6.1 Prepare SFT data

Create a source file such as `support_training.jsonl`:

```json
{"instruction":"How do I reset my password?","response":"Open Settings, choose Security, and select Reset Password."}
{"instruction":"How can I update my billing address?","response":"Open Billing, select Address, update the details, and save."}
{"instruction":"How do I contact support?","response":"Open Help Center and create a support ticket."}
```

Python:

```python
import tigerdatalab as td

tiger = td.create_project("SupportAI")

ai_project = tiger.ai_training(
    "SupportAI",
    task="sft",
)

dataset = ai_project.prepare(
    "support_training.jsonl",
    output_dir="./ai_dataset",
)
```

## 6.2 What output do I get?

TigerDataLab produces an AI dataset artifact directory:

```text
ai_dataset/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md
```

### `train.jsonl`

Contains the training portion of the prepared dataset.

Example:

```json
{"instruction":"How do I reset my password?","response":"Open Settings, choose Security, and select Reset Password."}
```

### `validation.jsonl`

Contains examples used for validation during model-development workflows.

### `test.jsonl`

Contains held-out examples for evaluation.

### `quality_report.json`

Machine-readable quality metadata for the generated dataset.

Conceptual example:

```json
{
  "source_records": 10000,
  "accepted_records": 9650,
  "rejected_records": 350,
  "duplicates_removed": 120,
  "quality_status": "pass"
}
```

The actual values depend on the source dataset.

### `lineage.json`

Records lineage information so the dataset can be traced back to its source/preparation process.

### `dataset_card.md`

Human-readable documentation describing the generated dataset.

## 6.3 Supported training-oriented tasks

TigerDataLab's AI dataset layer supports these task names:

| Task | Typical purpose | Example |
|---|---|---|
| `sft` | Supervised fine-tuning | Instruction → response |
| `instruction` | Instruction datasets | Task → answer |
| `dpo` | Preference optimization | Chosen vs rejected response |
| `classification` | Classification | Text → label |
| `text` | Plain text datasets | Documents / text corpus |

Example:

```python
ai_project = tiger.ai_training("SupportClassifier", task="classification")
dataset = ai_project.prepare("tickets.jsonl", output_dir="artifacts/tickets")
```

## 6.4 Dataset processing principles

The AI dataset pipeline is designed around:

```text
Source
  ↓
Normalization
  ↓
Quality validation
  ↓
PII/privacy-oriented masking
  ↓
Deduplication
  ↓
Canonicalization
  ↓
Deterministic splitting
  ↓
Train / validation / test
  ↓
Quality + lineage artifacts
```

Splits are deterministic so repeated preparation can be reproducible when the same inputs and configuration are used.

---

# 7. AI Model Training

TigerDataLab provides a model-agnostic training interface and a built-in Transformers SFT backend.

## 7.1 Create a trainer

```python
trainer = ai_project.trainer(
    model="your-compatible-model",
    output_dir="./company-model",
)
```

## 7.2 Train

```python
trainer.train_sft(
    dataset,
    epochs=3,
    batch_size=2,
)
```

The training layer can use the compatible backend to perform model training.

## 7.3 Training output

The exact model files depend on the backend and model configuration. A typical output directory may contain artifacts such as:

```text
company-model/
├── config.json
├── tokenizer files
├── model weights / adapter weights
├── training state
└── trainer metadata
```

The exact filenames are determined by the training stack and model.

## 7.4 LoRA / PEFT

The underlying TRL/Transformers ecosystem supports parameter-efficient fine-tuning approaches such as PEFT/LoRA where compatible with the selected model and backend.

Example configuration can be passed through the trainer:

```python
trainer.train_sft(
    dataset,
    epochs=3,
    batch_size=2,
    # pass backend/model-specific supported options here
)
```

> Do not assume every model supports every fine-tuning method. Model architecture, tokenizer, licensing, hardware and backend compatibility must be checked first.

## 7.5 What TigerDataLab does vs the model provider

```text
TigerDataLab
     ↓
Prepare + validate dataset
     ↓
Training interface
     ↓
Compatible training backend
     ↓
Model weights / adapters
```

TigerDataLab does **not** claim that every proprietary hosted model can have its weights modified. Hosted APIs may support inference or provider-specific fine-tuning instead.

---

# 8. Company AI / RAG

Company knowledge often changes more frequently than model weights.

Use the Company AI layer to provide current company information through retrieval/context rather than retraining the model for every policy change.

## 8.1 Create a Company AI project

```python
import tigerdatalab as td

tiger = td.create_project("AcmeAI")
company = tiger.company_ai("AcmeAI")
```

## 8.2 Add company knowledge

```python
company.add_knowledge(
    "HR Policy",
    "Employees receive 18 annual leaves per year.",
    department="HR",
    version="2026-01",
)
```

You can add more knowledge:

```python
company.add_knowledge(
    "AP Policy",
    "Invoices above INR 100000 require two approvals.",
    department="Accounts Payable",
)

company.add_knowledge(
    "Vendor Policy",
    "New vendors must have a valid tax identifier before activation.",
)
```

## 8.3 Connect an AI provider

```python
from tigerdatalab.ai.providers import OpenAIProvider

provider = OpenAIProvider()

company.connect(
    provider,
    model="your-model",
    system="You are the Acme company assistant. Follow company policy.",
)
```

Other built-in provider adapters include:

- OpenAI-compatible providers
- OpenAI
- Anthropic
- Gemini
- Groq
- OpenRouter
- Mistral
- Together

Credentials are read from supported environment variables or can be passed explicitly through the provider configuration.

## 8.4 Ask a company question

```python
answer = company.ask(
    "How many annual leaves do employees receive?"
)

print(answer.output)
```

Example output:

```text
Employees receive 18 annual leaves per year.
```

The returned `AIResult` contains structured fields such as:

```python
print(answer.output)
print(answer.model)
print(answer.context)
print(answer.tool_results)
```

Conceptually:

```text
AIResult
├── output        → model answer
├── model         → model/provider identifier when available
├── context       → knowledge/context supplied to the model
└── tool_results  → tool results when available
```

## 8.5 Why RAG instead of fine-tuning?

Use RAG/knowledge retrieval when information changes frequently:

```text
HR policy changed
       ↓
Update company knowledge
       ↓
No model retraining required
       ↓
AI can use the new context
```

Typical RAG use cases:

- HR policies
- SOPs
- product documentation
- finance policies
- customer-support knowledge
- current operational rules
- internal process documentation

---

# 9. Company AI Agent

`CompanyAgent` combines company knowledge, training preparation, model connection, tools, workflows and evaluation.

Create one through the project API:

```python
import tigerdatalab as td

project = td.create_project("Acme")
agent = project.company_agent("acme-ap-agent")
```

The intended lifecycle is:

```text
1. PREPARE  → training data
2. TEACH    → optional compatible fine-tuning
3. REMEMBER → company knowledge / RAG
4. ACT      → allow-listed tools + workflows
5. PROVE    → evaluation
```

## 9.1 Prepare agent training data

```python
agent.prepare_training(
    "company_training.jsonl",
    task="sft",
    output_dir="artifacts/acme_ap",
)
```

Output:

```text
artifacts/acme_ap/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md
```

## 9.2 Optionally train a compatible model

```python
agent.train(
    model="your-compatible-model",
    output_dir="models/acme-ap",
    epochs=3,
    batch_size=2,
)
```

Skip fine-tuning if RAG + tools + workflow logic are sufficient for the use case.

## 9.3 Add company knowledge

```python
agent.add_knowledge(
    "ap_policy.txt",
    "Invoices above INR 100000 require two approvals.",
    department="Accounts Payable",
)

agent.add_knowledge(
    "vendor_policy.txt",
    "New vendors must have a valid tax identifier before activation.",
)
```

## 9.4 Connect a model

```python
from tigerdatalab.ai.providers import OpenAIProvider

agent.connect(
    OpenAIProvider(),
    model="your-model",
    system="You are the Acme Accounts Payable assistant. Follow company policy.",
)
```

## 9.5 Ask the agent

```python
result = agent.ask(
    "Check invoice INV-10482 against the AP policy."
)

print(result.output)
```

Example output:

```text
Invoice INV-10482 is above the INR 100000 threshold and therefore requires two approvals.
```

The exact answer depends on the model, company context and registered tools.

---

# 10. AI Tools

Tools allow an AI application to interact with controlled business functions.

TigerDataLab uses an explicit allow-list approach.

## 10.1 Define a business function

```python
def get_invoice(invoice_id: str):
    # Replace with your ERP/database/API integration.
    return {
        "invoice_id": invoice_id,
        "amount": 125000,
        "status": "pending",
    }
```

## 10.2 Register the function as a Tool

```python
from tigerdatalab.ai.tools import Tool

invoice_tool = Tool(
    name="get_invoice",
    description="Retrieve invoice information by invoice ID.",
    function=get_invoice,
    parameters={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"}
        },
        "required": ["invoice_id"],
    },
)

agent.add_tool(invoice_tool)
```

## 10.3 Execute the registered tool explicitly

```python
result = agent.tools.execute(
    "get_invoice",
    {"invoice_id": "INV-10482"},
)

print(result)
```

Example output:

```python
{
    "invoice_id": "INV-10482",
    "amount": 125000,
    "status": "pending"
}
```

The tool result remains structured data and can be consumed by the surrounding application.

## 10.4 Tool schema

Tools expose an OpenAI-style function schema:

```python
print(invoice_tool.schema())
```

Conceptual output:

```json
{
  "type": "function",
  "function": {
    "name": "get_invoice",
    "description": "Retrieve invoice information by invoice ID.",
    "parameters": {
      "type": "object",
      "properties": {
        "invoice_id": {"type": "string"}
      },
      "required": ["invoice_id"]
    }
  }
}
```

## 10.5 Security model

The tool registry is explicit:

```text
AI model
   ↓
Tool request / decision
   ↓
Registered allow-listed tool
   ↓
Application function
   ↓
Structured result
```

The model is not given unrestricted Python execution.

> **Current scope:** TigerDataLab provides the tool contract, registry and controlled execution primitives. The current CompanyAgent does not implement an unrestricted autonomous tool-call loop that blindly executes arbitrary model-generated code.

---

# 11. Business Workflows

AI reasoning should not replace deterministic business rules when a process must be controlled.

TigerDataLab provides workflow primitives that can be attached to a CompanyAgent.

## 11.1 Create a workflow

```python
from tigerdatalab.ai.workflows import Workflow

workflow = Workflow(
    name="invoice_review",
)

agent.set_workflow(workflow)
```

## 11.2 Run the agent workflow

```python
result = agent.run({
    "invoice_id": "INV-10482",
})

print(result)
```

A business process can be structured like:

```text
Invoice received
      ↓
Validate invoice
      ↓
Get invoice data
      ↓
Check vendor
      ↓
Check approval policy
      ↓
AI reasoning / classification
      ↓
Flag exception or continue
      ↓
Business result
```

The important architectural principle is:

```text
AI = reasoning / language / classification
Business workflow = controlled execution
```

---

# 12. Model Routing

TigerDataLab includes a model-routing layer for applications that have multiple model targets.

A routing configuration can consider:

- provider
- model
- cost weight
- latency weight
- capabilities
- estimated cost
- estimated latency
- health/circuit-breaker state

Supported strategy concepts include:

```text
ordered
cost
latency
balanced
```

Aliases include concepts such as:

```text
first
fallback
fast
cheap
```

A routing system can therefore support an architecture such as:

```text
                 User Request
                      ↓
                 Model Router
          ┌───────────┼───────────┐
          ↓           ↓           ↓
       Model A      Model B     Model C
       cheaper       faster     fallback
          └───────────┼───────────┘
                      ↓
                   Result
```

> Cost and latency values are application estimates/configuration, not guaranteed live provider pricing or live latency measurements.

---

# 13. Evaluation

An AI system should be tested with representative business cases before production use.

## 13.1 Create evaluation records

```python
records = [
    {
        "prompt": "What is the approval threshold?",
        "expected": "Invoices above INR 100000 require two approvals.",
    },
    {
        "prompt": "What does a new vendor need before activation?",
        "expected": "A valid tax identifier.",
    },
]
```

## 13.2 Evaluate the agent

```python
result = agent.evaluate(records)
print(result)
```

Evaluation should answer questions such as:

```text
Did the agent answer correctly?
Did it follow company policy?
Did it use the expected context?
Did it fail on an edge case?
Did a workflow produce the correct business result?
```

## 13.3 Recommended improvement loop

```text
Build
  ↓
Evaluate
  ↓
Find failures
  ↓
Improve data / knowledge / prompt / workflow
  ↓
Evaluate again
  ↓
Release only after acceptable results
```

Do not treat a single successful response as proof that an AI system is production-ready.

---

# 14. End-to-End Company AI Example

The following example combines the major layers.

```python
import tigerdatalab as td
from tigerdatalab.ai.providers import OpenAIProvider
from tigerdatalab.ai.tools import Tool

# ---------------------------------------------------------
# 1. Create project and Company AI Agent
# ---------------------------------------------------------
project = td.create_project("Acme")
agent = project.company_agent("acme-ap-agent")

# ---------------------------------------------------------
# 2. Prepare company training data
# ---------------------------------------------------------
agent.prepare_training(
    "data/ap_training.jsonl",
    task="sft",
    output_dir="artifacts/ap_dataset",
)

# ---------------------------------------------------------
# 3. Optional model training
# ---------------------------------------------------------
# agent.train(
#     model="your-compatible-model",
#     output_dir="models/acme-ap",
#     epochs=3,
# )

# ---------------------------------------------------------
# 4. Add current company knowledge
# ---------------------------------------------------------
agent.add_knowledge(
    "ap_policy.txt",
    "Invoices above INR 100000 require two approvals.",
)

agent.add_knowledge(
    "vendor_policy.txt",
    "New vendors must have a valid tax identifier before activation.",
)

# ---------------------------------------------------------
# 5. Add controlled business tool
# ---------------------------------------------------------
def get_invoice(invoice_id: str):
    return {
        "invoice_id": invoice_id,
        "amount": 125000,
        "status": "pending",
    }

agent.add_tool(Tool(
    name="get_invoice",
    description="Retrieve invoice information.",
    function=get_invoice,
    parameters={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"}
        },
        "required": ["invoice_id"],
    },
))

# ---------------------------------------------------------
# 6. Connect a model
# ---------------------------------------------------------
agent.connect(
    OpenAIProvider(),
    model="your-model",
    system="You are an Accounts Payable assistant. Follow company policy.",
)

# ---------------------------------------------------------
# 7. Ask the agent
# ---------------------------------------------------------
answer = agent.ask("Review invoice INV-10482 against company policy.")

print("ANSWER:")
print(answer.output)
print("MODEL:")
print(answer.model)
print("CONTEXT:")
print(answer.context)
```

A possible application-level result is:

```text
ANSWER:
Invoice INV-10482 is pending and has an amount of INR 125000.
According to the AP policy, invoices above INR 100000 require two approvals.

MODEL:
your-model

CONTEXT:
[Relevant company knowledge supplied to the model]
```

The exact response depends on the selected provider/model and the configured knowledge.

---

# 15. Output Files and Artifacts

One of the most important differences between a simple AI demo and an engineering workflow is knowing **what gets produced and where it goes**.

## AI dataset preparation

When using:

```python
ai_project.prepare(
    "support_training.jsonl",
    output_dir="./ai_dataset",
)
```

expect the AI dataset artifact directory to contain:

```text
ai_dataset/
├── train.jsonl          # training records
├── validation.jsonl     # validation records
├── test.jsonl           # held-out test records
├── quality_report.json  # machine-readable quality information
├── lineage.json         # preparation/source lineage
└── dataset_card.md      # human-readable dataset documentation
```

## Pipeline manifest

When using:

```python
pipeline.save_manifest("pipeline_manifest.json")
```

you receive:

```text
pipeline_manifest.json
```

which records the configured pipeline steps.

## Model training

When training succeeds, the selected backend writes model/training artifacts to the configured `output_dir`.

```text
models/
└── company-model/
    └── backend/model artifacts
```

The exact files depend on the model and backend.

---

# 16. Supported Inputs

Core loading supports common structured formats including:

| Format | Typical use |
|---|---|
| CSV | Business exports, analytics datasets |
| JSON | APIs, structured records |
| JSONL | AI training/instruction datasets |
| Excel `.xlsx` / `.xls` | Finance, operations, business reports |
| Parquet | Analytics and larger data workflows |

For AI training, JSONL is particularly convenient because each line can represent one training example.

Example:

```jsonl
{"instruction":"Question 1","response":"Answer 1"}
{"instruction":"Question 2","response":"Answer 2"}
{"instruction":"Question 3","response":"Answer 3"}
```

---

# 17. Recommended Production Architecture

```text
                         COMPANY DATA
                              ↓
                    ┌──────────────────┐
                    │ Data Engineering │
                    └────────┬─────────┘
                             ↓
                    Data Quality / PII
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
         Analytics                     Data Science
              │                             │
              └──────────────┬──────────────┘
                             ↓
                       TRUSTED DATA
                             ↓
                    AI DATASET BUILDER
                             ↓
              ┌──────────────┴──────────────┐
              ↓                             ↓
       GENERAL AI TRAINING             COMPANY AI
                                            ↓
                                     RAG / KNOWLEDGE
                                            ↓
                                      MODEL ROUTER
                                            ↓
                                    TOOLS / WORKFLOW
                                            ↓
                                        EVALUATION
                                            ↓
                                   APPLICATION LAYER
```

A production deployment can place TigerDataLab inside a larger application architecture:

```text
                 Web / Mobile / Internal App
                              ↓
                         API Service
                              ↓
                       TigerDataLab
                  ┌───────────┼───────────┐
                  ↓           ↓           ↓
               Data       Company AI    Evaluation
             pipeline       Agent
                  ↓           ↓
             Database      Provider APIs
                              ↓
                       Business systems
```

TigerDataLab is the Python library/data-AI layer; your application remains responsible for authentication, authorization, networking, deployment infrastructure, database permissions and operational monitoring.

---

# 18. Security and Safety

Company AI should be designed with least privilege.

## Recommended controls

```text
User authentication
        ↓
Authorization
        ↓
Application API
        ↓
TigerDataLab
        ↓
Allow-listed tools
        ↓
Approved business systems
```

## Do not expose unrestricted access

Avoid giving an AI model:

- unrestricted shell access
- unrestricted filesystem access
- unrestricted database write access
- arbitrary code execution
- production credentials

Instead:

```text
AI
 ↓
Explicit tool
 ↓
Validated arguments
 ↓
Authorized business function
 ↓
Audited result
```

## PII

Training data may contain sensitive information. Use appropriate organizational privacy controls and review generated datasets before training or sharing them.

TigerDataLab's AI data pipeline includes privacy-oriented processing, but organizations remain responsible for deciding what data is legally and operationally appropriate to process.

---

# 19. Project Structure

The package is organized around separate data and AI responsibilities.

```text
tigerdatalab/
├── __init__.py
├── platform.py
├── core/
├── data/
├── ai/
│   ├── agent.py
│   ├── dataset.py
│   ├── providers.py
│   ├── router.py
│   ├── system.py
│   ├── tools.py
│   ├── training.py
│   └── workflows.py
└── ...
```

The public API is exposed through `tigerdatalab` and project-oriented objects such as:

```python
TigerDataLab
DataPipeline
DataScience
DatasetProfile
AIProject
CompanyAIProject
```

Company agents are created through:

```python
project.company_agent("agent-name")
```

---

# 20. Important Scope and Limitations

TigerDataLab is designed to be practical and explicit about what it does.

## Training

TigerDataLab provides:

- AI dataset preparation
- validation and quality artifacts
- deterministic splits
- lineage
- training interfaces
- a Transformers/TRL-oriented SFT backend

It does not magically fine-tune every proprietary hosted model.

## RAG

The Company AI layer can carry company knowledge/context, but a complete production retrieval infrastructure may require your chosen vector database, document store, embedding system or search service.

## Tools

TigerDataLab provides controlled tool definitions and execution primitives. The current CompanyAgent is not an unrestricted autonomous agent that executes arbitrary model-generated code.

## Deployment

TigerDataLab is a Python library and application building block. It is not itself a hosted SaaS deployment platform.

Your application is responsible for:

- API hosting
- authentication
- authorization
- secrets management
- database infrastructure
- cloud/container deployment
- logging and monitoring
- network security

## Model cost and latency

Router cost/latency settings are configuration estimates. They should not be treated as guaranteed live provider measurements.

---

# 21. API Quick Reference

## Top-level API

```python
import tigerdatalab as td
```

Common exports include:

```python
# Package version
print(td.__version__)

# Core analysis
result = td.analyze("data.csv")

# Open/load data
frame = td.open("data.csv")

# Large-data entry point
frame = td.large("data.parquet")

# Profile
profile = td.profile(frame)

# Quality check
quality = td.quality_check("data.csv")

# Clean file
cleaned = td.clean_file("raw.xlsx", output_path="clean.xlsx")

# Project
project = td.create_project("MyProject")
```

## Project API

```python
project.load(source)
project.profile(frame)
project.analyze(source)
project.ai_training(name, task="sft")
project.company_ai(name)
project.company_agent(name)
```

## Data engineering

```python
pipeline = project.engineering
pipeline.add(name, transform)
pipeline.run(frame)
pipeline.save_manifest(path)
```

## Data science

```python
project.data_science.profile(frame)
project.data_science.correlation(frame)
project.data_science.train_test_split(
    frame,
    test_size=0.2,
    seed=42,
)
```

## AI training

```python
ai_project = project.ai_training("MyAI", task="sft")

dataset = ai_project.prepare(
    "training.jsonl",
    output_dir="artifacts/dataset",
)

trainer = ai_project.trainer(
    model="your-compatible-model",
    output_dir="models/my-model",
)
```

## Company AI

```python
company = project.company_ai("CompanyAI")
company.add_knowledge(source, text, **metadata)
company.connect(provider, model, system=None)
company.ask(prompt)
company.run(inputs=None)
```

## Company Agent

```python
agent = project.company_agent("agent")

agent.prepare_training(...)
agent.train(...)
agent.add_knowledge(...)
agent.add_tool(...)
agent.connect(...)
agent.set_workflow(...)
agent.ask(...)
agent.run(...)
agent.evaluate(...)
```

---

# Quick Start: From CSV to Company AI

If you want to understand TigerDataLab in one example, use this mental model:

```python
import tigerdatalab as td

# 1. Load business data
project = td.create_project("MyCompany")
df = project.load("customers.csv")

# 2. Understand it
profile = project.profile(df)

# 3. Prepare AI training data
ai = project.ai_training("SupportAI", task="sft")
dataset = ai.prepare(
    "support_training.jsonl",
    output_dir="artifacts/support-ai",
)

# 4. Create company AI
company = project.company_ai("CompanyAssistant")
company.add_knowledge(
    "HR Policy",
    "Employees receive 18 annual leaves per year.",
)

# 5. Connect a model/provider
# company.connect(provider, model="your-model")

# 6. Ask business questions
# result = company.ask("How many annual leaves do employees receive?")
# print(result.output)
```

The result of the overall workflow is not just one answer. You get reusable artifacts and structured objects at each stage:

```text
DATA STAGE
├── DataFrame
├── DatasetProfile
├── Quality result
└── Cleaned data

AI DATA STAGE
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── quality_report.json
├── lineage.json
└── dataset_card.md

AI APPLICATION STAGE
├── CompanyAI / CompanyAgent
├── knowledge/context
├── registered tools
├── workflows
└── AIResult
```

---

# Philosophy

TigerDataLab follows one simple idea:

> **Don’t replace your AI. Teach it your data, your rules, and your workflow.**

A strong company AI system is usually not only a model.

It is:

```text
GOOD DATA
   +
GOOD KNOWLEDGE
   +
GOOD PROMPTS
   +
CONTROLLED TOOLS
   +
DETERMINISTIC WORKFLOWS
   +
REPEATABLE EVALUATION
   =
RELIABLE AI APPLICATION
```

---

# License

See the repository `LICENSE` file for the applicable license.

# Links

- [GitHub Repository](https://github.com/abhi15724/tigerdatalab)
- [PyPI Package](https://pypi.org/project/tigerdatalab/)
- [CI Workflow](https://github.com/abhi15724/tigerdatalab/actions/workflows/ci.yml)

---

<div align="center">

**🐯 TigerDataLab — From Raw Data to Production AI**

</div>
