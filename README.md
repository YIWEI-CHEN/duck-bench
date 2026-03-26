# 🦆 DUCK: Beyond Text-to-SQL — Benchmarking Cross-modal Knowledge Grounding over Enterprise Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Dataset](https://img.shields.io/badge/Dataset-Coming%20Soon-lightgrey)](#)

**DUCK** (**D**ataverse **U**nified **C**ross-modal **K**nowledge-grounding) is a large-scale benchmark for evaluating the ability of language models to ground natural language questions over heterogeneous enterprise data. Unlike existing text-to-SQL benchmarks that focus on clean relational tables, DUCK challenges models to reason across the full spectrum of data modalities found in real-world enterprise environments.

---

## Why DUCK?

Existing text-to-SQL benchmarks (Spider, BIRD, WikiSQL) have driven remarkable progress — but they share a critical blind spot: **real enterprise data is not just relational tables.**

In platforms like Microsoft Dataverse, a single user question may require joining CRM records, filtering log streams, searching through uploaded files, parsing multi-line text fields, or extracting action items from meeting transcripts — all in one query.

DUCK is designed to close this gap.

| Dimension | Spider | BIRD | DUCK |
|-----------|--------|------|------|
| Tables | 200+ | 95 | **500+** |
| Data modality | Relational only | Relational only | **Cross-modal** |
| CRM data | ✗ | ✗ | ✔ |
| File attachments | ✗ | ✗ | ✔ |
| System logs | ✗ | ✗ | ✔ |
| Multi-line text fields | ✗ | ✗ | ✔ |
| Meeting recaps | ✗ | ✗ | ✔ |
| Enterprise schema complexity | Low | Medium | **High** |

---

## Data Modalities

DUCK covers **7 cross-modal data categories** that reflect real enterprise usage:

### 1. Large-Scale Relational Data
Hundreds of interconnected tables with complex foreign key relationships, polymorphic joins, and hierarchical entity structures typical of Dataverse environments.

### 2. CRM Data
Accounts, contacts, leads, opportunities, and cases with domain-specific semantics — e.g., "Which accounts in the West region have open opportunities over $100K with no activity in the last 30 days?"

### 3. Relational Data with Business Logic
Tables encoding business rules, status transitions, approval workflows, and computed fields that require understanding of enterprise-specific logic beyond schema-level joins.

### 4. File Attachments
Queries that require reasoning over metadata and content of files stored as annotations or attachments — e.g., "Find all contracts uploaded to closed-won opportunities that mention indemnification clauses."

### 5. System & Audit Logs
Structured log data capturing user actions, system events, and change history — e.g., "Which users modified the pricing field on any opportunity more than 3 times last quarter?"

### 6. Multi-Line Text Fields
Rich-text and multi-line fields (notes, descriptions, email bodies) that require text parsing, pattern extraction, or keyword search within structured query context.

### 7. Meeting Recaps & Transcripts
Semi-structured meeting summaries and transcripts linked to CRM entities — e.g., "Summarize action items from all customer calls related to the Contoso renewal this month."

---

## Benchmark Structure

```
duck-bench/
├── pyproject.toml            # Project metadata & dependencies (uv)
├── uv.lock                   # Lockfile
├── data/
│   ├── databases/            # Dataverse-style database snapshots
│   │   ├── crm_sales/
│   │   ├── crm_service/
│   │   ├── project_ops/
│   │   └── ...
│   ├── questions/
│   │   ├── train.json        # Training split
│   │   ├── dev.json          # Development split
│   │   └── test.json         # Held-out test split (labels hidden)
│   └── files/                # Attached documents, logs, transcripts
├── evaluation/
│   ├── evaluate.py           # Evaluation script
│   ├── metrics.py            # Metric implementations
│   └── exec_engine.py        # Execution-based evaluation engine
├── baselines/
│   ├── gpt4/
│   ├── claude/
│   ├── llama/
│   └── t5/
└── guides/
    ├── annotation_guide.md
    ├── schema_docs.md
    └── dataverse_primer.md
```

---

## Question Format

Each question instance contains:

```json
{
  "question_id": "DUCK_0001",
  "question": "Which sales reps closed more than $500K in Q3 but have no meeting recaps logged for any of those deals?",
  "evidence": "Q3 refers to July 1 – September 30. Meeting recaps are stored in the annotation table with object_type = 'meeting_recap'.",
  "SQL": "SELECT sr.name, SUM(o.actual_value) AS total_closed FROM ...",
  "db_id": "crm_sales",
  "modality": ["relational", "crm", "meeting_recap"],
  "difficulty": "challenging",
  "tags": ["multi-table", "temporal", "cross-modal"]
}
```

### Difficulty Levels

| Level | Description |
|-------|-------------|
| **Simple** | Single modality, ≤3 tables, straightforward filters |
| **Moderate** | 2 modalities, 3–6 tables, aggregations or subqueries |
| **Challenging** | 3+ modalities, 6+ tables, complex joins with business logic |
| **Expert** | Cross-modal reasoning, ambiguous schema, requires domain knowledge |

---

## Evaluation Metrics

DUCK uses a multi-dimensional evaluation framework:

| Metric | Description |
|--------|-------------|
| **Execution Accuracy (EX)** | Does the predicted SQL return the correct result set? |
| **Valid Efficiency Score (VES)** | Execution accuracy weighted by query efficiency |
| **Modality Coverage (MC)** | Fraction of required data modalities correctly accessed |
| **Schema Linking F1** | Precision/recall of table and column references |
| **Soft F1** | Token-level F1 for free-text extraction tasks |

### Running Evaluation

```bash
# Run evaluation on dev set
uv run python evaluation/evaluate.py \
  --predicted predictions/dev_pred.json \
  --gold data/questions/dev.json \
  --db_dir data/databases/ \
  --metrics ex ves mc
```

---

## Baselines

We provide baseline results for several state-of-the-art models:

| Model | EX (%) | VES (%) | MC (%) | Simple | Moderate | Challenging | Expert |
|-------|--------|---------|--------|--------|----------|-------------|--------|
| GPT-4o | — | — | — | — | — | — | — |
| Claude Sonnet | — | — | — | — | — | — | — |
| Llama 3 70B | — | — | — | — | — | — | — |
| T5-3B (fine-tuned) | — | — | — | — | — | — | — |
| DIN-SQL + GPT-4o | — | — | — | — | — | — | — |

> Baseline numbers will be populated upon release. We welcome community submissions.

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-org/duck-bench.git
cd duck-bench
```

### 2. Set up the environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

### 3. Download the data

```bash
# From HuggingFace
uv run python scripts/download_data.py --source huggingface

# Or manually
# Download from https://huggingface.co/datasets/duck-bench
```

### 4. Run a baseline

```bash
uv run python baselines/run_baseline.py \
  --model gpt-4o \
  --split dev \
  --output predictions/gpt4o_dev.json
```

### 5. Evaluate

```bash
uv run python evaluation/evaluate.py \
  --predicted predictions/gpt4o_dev.json \
  --gold data/questions/dev.json \
  --db_dir data/databases/
```

---

## Leaderboard

We host a public leaderboard for test set evaluation. Submit your predictions:

```bash
uv run python scripts/submit.py \
  --predicted predictions/test_pred.json \
  --model_name "YourModel" \
  --team "YourTeam"
```

🏆 Leaderboard: [yiwei-chen.github.io/duck-bench](https://yiwei-chen.github.io/duck-bench)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- **New questions**: Follow our [annotation guide](guides/annotation_guide.md)
- **New databases**: Submit Dataverse-compatible schema snapshots
- **New baselines**: Add your model under `baselines/` with a config file
- **Bug fixes**: Open an issue or PR

---

## Citation

```bibtex
@misc{duck2026,
  title={DUCK: Beyond Text-to-SQL --- Benchmarking Cross-modal Knowledge Grounding over Enterprise Data},
  author={Yi-Wei Chen},
  howpublished={\url{https://github.com/your-org/duck-bench}},
  year={2026}
}
```

> 📄 Paper coming soon. We will update the citation with an arXiv link once available.

---

## TODO

- [ ] Prepare Dataverse environment (dev/sandbox)
- [ ] Design and create Dataverse tables matching benchmark schemas
- [ ] Load benchmark data into Dataverse
- [ ] Build Dataverse connection utilities (`tools/`)
- [ ] Implement evaluation pipeline against live Dataverse
- [ ] Generate benchmark questions across all 7 modalities
- [ ] Run baseline models and populate leaderboard
- [ ] Publish dataset to HuggingFace
- [ ] Write and submit paper

---

## License

The DUCK benchmark is released under the [MIT License](LICENSE). The underlying database schemas are derived from public Dataverse documentation and sample data.

---

## Acknowledgments

DUCK builds on the pioneering work of the [Spider](https://yale-lily.github.io/spider), [BIRD](https://bird-bench.github.io/), and [WikiSQL](https://github.com/salesforce/WikiSQL) benchmarks. We thank the text-to-SQL research community for establishing the foundations that made this work possible.

---

<p align="center">
  <b>🦆 DUCK</b> — because enterprise data doesn't fit in a single table.
</p>
