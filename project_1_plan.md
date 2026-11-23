# Project-I: Graph-Based Knowledge Graph for Research Collaboration Analysis

## Purpose

This document turns the supplied project overview into an actionable project plan. The overview is the source for the proposed project title, problem, broad methods, and semester sequence. The research scope and milestones below are recommendations to confirm with the project supervisor.

## What the supplied overview says

The project aims to represent relationships among scholarly entities and analyze research collaboration. It proposes bibliographic metadata sources such as DBLP, Crossref, Semantic Scholar, ORCID, and institutional repositories; entity extraction and preprocessing; a graph database such as Neo4j; graph analysis and community detection; evaluation; and visualization.

The semester-wise sequence shown is:

- **Project-I:** literature review, identify gaps, collect bibliographic data, preprocess metadata, perform entity extraction, and design the graph database schema.
- **Project-II:** construct the knowledge graph, implement graph clustering/community detection, analyze networks, create visualizations, and build the collaboration analysis module.
- **Project-III:** implement collaborator recommendation, evaluate/optimize, build a web dashboard, document, and deploy the prototype.

The image is a project description. It does not contain a publication dataset or define a specific research field, date range, or sample size.

## Proposed scope to confirm with the supervisor

- **Research field:** Artificial Intelligence and Machine Learning publications.
- **Proposed period:** 2016–2025 inclusive.
- **Pilot:** approximately 100 records to assess query quality and metadata coverage.
- **Working dataset target:** 2,000–5,000 works, adjusted after the pilot and supervisor approval.
- **Primary source:** OpenAlex, because its linked scholarly records include works, authors, sources, institutions, and topics. Its API supports search, filters, selection of fields, and pagination. A free key is recommended for larger retrievals and is required for cursor paging beyond the first page. See [OpenAlex API reference](https://help.openalex.org/api/) and [authentication and paging limits](https://help.openalex.org/api/authentication/).
- **Optional cross-check:** Crossref for DOI-based metadata verification. Crossref records reflect metadata deposited with Crossref; use it only where useful. See [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/).

These scope choices are suggestions, not requirements from the supplied overview. If the student selects another domain, revise the search strategy and dataset scope before the full collection.

## Research question (working draft)

**How have co-author communities and topic connections in AI and Machine Learning research changed from 2016 through 2025?**

Possible subquestions:

1. Which authors and institutions are most connected in the selected corpus?
2. What collaboration communities appear under a documented community-detection method?
3. How do the topics represented by these communities change over time?

The final question should be narrowed and approved by the supervisor after the literature review and pilot.

## Dataset extraction specification

### Collection procedure

1. Define and record the exact search query, publication years, work types, and inclusion/exclusion rules.
2. Run the query on a pilot of approximately 100 records.
3. Inspect whether the results are relevant and whether the required metadata is present. Revise the query if needed and record each change.
4. Collect the agreed full corpus from OpenAlex. Preserve raw responses without overwriting them.
5. Store the query, retrieval date, source, API version or endpoint, and any pagination details in a collection log.
6. Use a free API key for larger collection where appropriate; keep it out of source code and published files. Respect API limits and retry guidance.
7. Optionally verify DOI records against Crossref. Preserve source provenance and do not silently replace conflicting values.

### Suggested fields

For each work, retain where available:

- OpenAlex work ID (stable source identifier)
- DOI
- title
- publication year and date
- work type
- venue/source name and ID
- author names and OpenAlex author IDs
- author affiliations and institution IDs
- topics and topic IDs
- abstract or abstract availability indicator, subject to source access and project needs
- citation count and retrieval date, if used in analysis

### Cleaning and quality rules

- Keep a read-only raw dataset and write cleaned outputs separately.
- Deduplicate by normalized DOI when present; otherwise use the OpenAlex work ID. Flag likely title/year duplicates for review rather than deleting uncertain matches automatically.
- Preserve source IDs for authors and institutions. Do not merge people based on name alone.
- Normalize whitespace and text consistently while retaining original source values where practical.
- Represent missing fields as missing; do not invent affiliations, topics, or identifiers.
- Track counts before and after each cleaning step and keep a reproducible log.
- Inspect a manually selected sample of records and entity links; report errors and limitations.

### Suggested data outputs

- `works.csv` — one row per work
- `authors.csv` — one row per author entity
- `institutions.csv` — one row per institution entity, if available
- `venues.csv` — one row per publication source
- `topics.csv` — one row per topic
- `authorships.csv` — work-to-author links, including author position if available
- `affiliations.csv` — author/work-to-institution links where supplied
- `work_topics.csv` — work-to-topic links
- `data_dictionary.md` — field definitions, source, and known caveats
- `collection_log.md` — query, date, source, and collection notes

## Initial graph schema

```text
(Author)-[:AUTHORED {position}]->(Paper)
(Paper)-[:PUBLISHED_IN]->(Venue)
(Paper)-[:HAS_TOPIC {score}]->(Topic)
(Author)-[:AFFILIATED_WITH]->(Institution)
```

Create an `Institution` node and affiliation edge only when source data supports it. Store stable source IDs as unique keys. The schema can be expanded after inspecting the pilot data.

## Year workflow and deliverables

Adjust month numbers to the department's academic calendar and submission dates.

| Period | Work | Deliverable / completion evidence |
|---|---|---|
| Month 1 | Confirm supervisor expectations, problem scope, research question, field, time range, and evaluation criteria. | Approved one-page proposal and milestone calendar |
| Months 2–3 | Review literature on scholarly knowledge graphs, collaboration networks, entity resolution, and community detection. Compare data sources and identify a defensible gap. | Literature matrix, review draft, documented source choice |
| Months 3–4 | Run the pilot collection; inspect relevance, missing values, duplicate rate, and entity coverage; refine inclusion rules. | Pilot dataset, query log, data dictionary draft, supervisor-approved collection specification |
| Months 4–5 | Collect the full dataset and preserve raw data. Build repeatable cleaning and deduplication steps. | Raw data snapshot, cleaned tables, reproducible pipeline, quality summary |
| Months 5–6 | Extract/link authors, works, institutions, venues, and topics; review ambiguous matches. Design and document the graph schema. | Entity/link tables, schema diagram, Project-I report and presentation |
| Months 7–8 | Load the knowledge graph; validate node/edge counts and sample paths. | Neo4j or equivalent graph, load scripts, validation notes |
| Months 8–9 | Generate co-authorship projections and calculate justified network measures. Run a selected method such as Louvain or Leiden with documented settings. | Analysis notebook/scripts, network measures, community results |
| Months 9–10 | Evaluate data quality and analytical results. Test robustness on samples or parameter choices; explain limitations. | Evaluation results and revised analysis |
| Months 10–11 | Build a clear graph exploration view or lightweight dashboard; focus on communicating findings. | Demonstrable visualization/dashboard |
| Month 12 | Complete report, presentation, documentation, reproducibility package, and next-step plan. | Final report, presentation, source/data documentation, demo |

## Evaluation plan

Use measures appropriate to what is actually implemented:

- **Dataset quality:** number of works, duplicate rate, missingness by field, date/topic coverage, and source provenance.
- **Entity/link quality:** manually inspect a sample of author, institution, and topic links; report precision and recall only if a labeled reference set is created.
- **Graph structure:** nodes/edges by type, degree distribution, connected components, and density where meaningful.
- **Community detection:** modularity and stability across reasonable parameter settings; qualitative inspection of representative communities. Do not treat modularity alone as proof of meaningful communities.
- **Link prediction (optional):** only if implemented; use a held-out split and report precision/recall or ranking metrics. Avoid data leakage across time or duplicated works.
- **Usability (optional):** task-based feedback on whether users can find communities, authors, or topics in the visualization.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Topic query returns irrelevant or incomplete papers | Pilot first; use explicit search terms and inclusion rules; report scope limits |
| Authors with similar names are merged, or one author is split across records | Prefer stable source IDs; do not resolve identity from name alone; manually review a sample |
| Affiliations or abstracts are missing | Make these optional fields; report missingness; avoid unsupported inference |
| Dataset is too large for the semester | Start with a fixed pilot and target size; narrow years or field if needed |
| Communities reflect corpus/query choices rather than the whole research field | State the sampling frame and test sensitivity to query and time window |
| API changes or limits disrupt collection | Save raw responses, log queries and dates, use conservative pagination and retries, keep a reproducible snapshot |

## Immediate checklist

- [ ] Confirm the field and research question with the supervisor.
- [ ] Confirm the academic year calendar, proposal/report format, and grading milestones.
- [ ] Create the literature matrix and start reading foundational/current papers.
- [ ] Test an OpenAlex search with 100 records and inspect returned metadata.
- [ ] Finalize the inclusion rules, fields, and target dataset size after the pilot.
- [ ] Draw the initial entity-relationship schema.
- [ ] Keep data provenance, privacy, source terms, and API key handling documented.

## Source references

- [OpenAlex API reference](https://help.openalex.org/api/)
- [OpenAlex authentication and paging limits](https://help.openalex.org/api/authentication/)
- [Crossref REST API documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)
