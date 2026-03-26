# DUCK: Dataverse Unified Cross-modal Knowledge-grounding

**"Beyond the Table: Can LLMs Generate SQL from Hybrid Enterprise Knowledge?"**

DUCK is a next-generation Text-to-SQL benchmark designed for the complex, "amphibious" nature of modern enterprise data. While existing benchmarks like BIRD focus primarily on large-scale relational databases, DUCK challenges models to perform **Cross-modal Knowledge-grounding** — synthesizing SQL queries from a mix of structured tables, semi-structured logs, and unstructured documents.

## Why DUCK?

In real-world platforms like Dataverse, data doesn't live in isolated tables. It is a messy, hybrid environment. DUCK evaluates the model's ability to "dive deep" into:

- **Massive Relational Schemas**: Environments with 100+ interconnected tables.
- **CRM Data**: Navigating complex business logic (Accounts, Leads, Opportunities).
- **Logs & Semi-structured Data**: Extracting query constraints from system logs.
- **Unstructured Files**: Grounding SQL filters based on external PDF/Docx content.
- **Multi-line Texts & Meeting Recaps**: Reasoning over long-form transcripts to define the true intent of a query.

## Benchmark Comparison

| Feature | Spider | BIRD | DUCK (Ours) |
|---|---|---|---|
| Primary Goal | Cross-domain | Large DB Efficiency | Hybrid Data Grounding |
| Data Diversity | Tables only | Tables only | Tables + Logs + Files + Meetings |
| Schema Complexity | Low-Medium | High | Extremely High (100+ Tables) |
| Reasoning Type | Syntactic | Database Logic | Cross-modal Semantic Reasoning |
| Real-world Context | Academic | Industrial DB | Enterprise Unified Knowledge |

## Repository Structure

```
duck-bench/
├── data/
│   ├── relational/       # 100+ Tables & CRM Data
│   ├── semi-structured/  # Logs, JSON exports
│   └── unstructured/     # Meeting recaps, Multi-line texts, Files
├── evaluation/           # Scoring scripts (Execution Accuracy, Valid Efficiency)
├── baselines/            # Prompts and scripts for GPT-4o, Claude 3.5, etc.
├── tools/                # Dataverse connection utilities
└── README.md
```
