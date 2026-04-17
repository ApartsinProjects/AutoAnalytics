# AutoAnalytics

![AutoAnalytics Hero](docs/figures/hero_top.png)

AutoAnalytics is a research project on **AI-native analytics design**: not only translating questions into SQL, but helping determine **which questions are meaningful and answerable** given the data that actually exists.

## Motivation

In many organizations, analytics bottlenecks happen before SQL:

- teams do not know what the database can reliably answer,
- KPI ideation is disconnected from real schema constraints,
- analysts spend time asking impossible or low-value questions.

AutoAnalytics focuses on this earlier and harder layer:

> **Given role context + available data, what are the highest-value questions we should ask?**

This requires explicit understanding of data availability, schema semantics, granularity, joins, and blind spots.

## The Core Research Question

Traditional BI workflows assume the question is already well-formed.  
AutoAnalytics studies the upstream problem:

- How can a system infer the *question space* from raw enterprise data?
- How can it map that question space to role-specific KPIs?
- How can it ensure generated queries are executable and decision-useful?

## Differentiation From Text2SQL

Text2SQL solves:  
`natural language question -> SQL query`

AutoAnalytics solves a broader loop:

`data understanding -> question discovery -> KPI design -> SQL generation -> validation -> insight + visualization`

That means AutoAnalytics is not just a query translator; it is a **question discovery and analytics orchestration framework**.

### Conceptual Diagram (Hero)

The hero image above is intentionally used as the project diagram:  
it communicates the transition from **data chaos** to **question clarity** to **decision confidence**, which is the core distinction between AutoAnalytics and classic Text2SQL systems.

## Conceptual System Flow

1. ingest role and organization context,
2. inspect source schema and data samples,
3. construct semantic schema understanding,
4. generate tasks and KPI candidates aligned with role intent,
5. synthesize SQL implementations,
6. validate and repair SQL when needed,
7. produce insight narratives and visual outputs.

## Why This Matters

If successful, this approach can reduce time-to-insight by shifting effort from manual dashboard bootstrapping to automated, data-grounded KPI and question generation. The goal is to help teams move from “What can we query?” to “What should we learn next?”

## Research Directions

- **Question-space quality**: are proposed questions relevant, novel, and actionable?
- **Feasibility alignment**: are generated KPIs computable from available data?
- **SQL reliability**: execution pass rate before/after repair loops.
- **Insight faithfulness**: are narratives supported by computed results?
- **Human utility**: does the system improve analyst productivity and decision speed?

## Repository Layout

```text
AutoAnalytics/
├─ src/                     # Core modules
├─ notebooks/               # Experimental/orchestration notebooks
├─ assets/styles/           # UI styles
├─ docs/figures/            # Gemini-generated conceptual visuals
├─ scripts/                 # Utility scripts
└─ README.md
```

## Generate Figures (Gemini)

```bash
# PowerShell
$env:GEMINI_API_KEY="YOUR_KEY"
python scripts/generate_gemini_figures.py
```

Outputs:

- `docs/figures/hero_top.png`

All images are conceptual communication assets intended for research presentation.
