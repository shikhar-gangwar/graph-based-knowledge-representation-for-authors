# Project - I Methodology: Bibliographic Data Ingestion, Entity Resolution & Graph Schema Design

**Project Title:** Graph-Based Knowledge Graph for Research Collaboration Analysis (Title 34)  
**Academic Phase:** Project - I (Methodology & Implementation)  
**Target Domain:** Artificial Intelligence & Machine Learning Research (2016–2025)  
**Primary Data Source:** OpenAlex REST API (Works, Authors, Institutions, Venues, Topics)  

---

## 1. Research Scope & Theoretical Framework

### 1.1 Context and Problem Formulation
Research collaboration analysis requires modeling complex, multi-entity relationships among authors, publications, research topics, affiliations, and publishing venues. Conventional co-authorship networks model homogeneous pairwise interactions ($Author \leftrightarrow Author$), discarding the rich semantic context of why and where collaborations occur.

This project designs and implements a **Heterogeneous Labeled Property Graph (LPG)** in Neo4j to capture the multi-dimensional structure of scholarly research.

### 1.2 Focused Research Questions (Project-I Foundation)
* **Primary RQ:** *How does a multi-entity knowledge graph integrating publications, canonical authors, institutional affiliations, and hierarchical topics capture collaboration patterns and interdisciplinary interfaces more accurately than homogeneous co-authorship projections?*
* **Sub-RQ 1 (Entity Resolution & Data Integrity):** What are the empirical missingness rates and identifier stability across bibliographic entities (DOIs, author IDs, ROR institution IDs), and how do deterministic fallback mechanisms preserve 100% referential integrity?
* **Sub-RQ 2 (Topological & Semantic Linkage):** How does multi-topic association (at topic and subfield granularity) contextualize collaborative clusters across the 2016–2025 deep learning decade?

---

## 2. Bibliographic Data Acquisition Architecture

### 2.1 Primary Source Justification: OpenAlex API
Following the audit of DBLP Discovery Dataset (D3)—which revealed a 52% false-positive rate from broad hierarchical CSO concepts and a temporal truncation at 2021—**OpenAlex** was selected as the primary source of truth:
1. **Current Taxonomy:** Utilizes OpenAlex's official 2024 Topics taxonomy. Subfield `1702` represents "Artificial Intelligence" under the "Computer Science" field and "Physical Sciences" domain.
2. **Temporal Coverage:** Complete, real-time index spanning 2016 through 2025 inclusive.
3. **Institutional Authority Control:** Direct integration with the Research Organization Registry (ROR) for institutional entity resolution.
4. **Open Access & Ethical Compliance:** Released under the Creative Commons CC0 public domain dedication.

### 2.2 Deterministic Year-Stratified Sampling Strategy
To prevent temporal bias (such as older papers dominating citation rankings or recent papers lacking citations), the sampling pipeline enforces a **deterministic year-stratified collection rule**:
$$\text{Corpus} = \bigcup_{y=2016}^{2025} \operatorname{Sample}_{500}(y)$$
- **Years:** 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 (10 strata).
- **Quota:** Exactly 500 works per year, yielding 5,000 total works.
- **Inclusion Filter:**
  - `primary_topic.subfield.id:1702` (Artificial Intelligence)
  - `publication_year:{year}`
  - `type:article|conference-paper|book-chapter`
  - `is_retracted:false` (excludes withdrawn research)
  - `is_paratext:false` (excludes covers, tables of contents, and editorial board listings)
- **Ranking Function:** `sort=cited_by_count:desc` within each year stratum to select influential anchor papers that seed dense collaboration and institutional ties.

---

## 3. Data Preprocessing & Entity Resolution Pipeline

### 3.1 Abstract Reconstitution
OpenAlex provides paper abstracts as an inverted index (`abstract_inverted_index`) mapping each unique token to an array of character/word positions. The preprocessing pipeline (`src/preprocess/process_openalex_5000.py`) sorts tokens by positional index to reconstruct clean continuous text:
$$\text{Abstract} = \operatorname{join}\left( \operatorname{sort}_{\text{pos}}\left( \{(p, w) \mid w \in \text{Index}, p \in \text{Index}[w]\} \right) \right)$$
Missing abstracts are preserved as empty strings; no synthetic text is generated.

### 3.2 Deduplication Protocol
Publications are deduplicated by:
1. Canonical OpenAlex Work ID (`W...`)
2. Normalized DOI (lowercase, stripped of `https://doi.org/` or `http://dx.doi.org/`)
- A hash table tracks observed IDs; duplicate records are discarded and logged.

### 3.3 Author Identity Resolution
- Authors are resolved using persistent OpenAlex Author IDs (`A...`).
- Authors with documented ORCIDs retain their verified digital identifier.
- If an author record in a raw response lacks an OpenAlex ID, a deterministic fallback ID is generated using an MD5 hash of the author display name and work ID:
  $$\text{ID}_{\text{fallback}} = \text{A\_anon\_} + \operatorname{MD5}(Name \parallel WorkID)[:10]$$
- **Rule:** Authors are **never merged using name string alone**, avoiding homonym collisions.
- **Privacy:** Author email addresses are completely excluded.

### 3.4 Institutional Resolution via ROR
- Institutional affiliations are mapped via canonical OpenAlex Institution IDs (`I...`).
- Official ROR URIs and ISO two-letter country codes are preserved.
- Authors with multiple affiliations on a given paper produce explicit relational edges to each institution.

---

## 4. Graph Database Schema & Storage Architecture

### 4.1 Labeled Property Graph (LPG) Design
The graph model is implemented in Neo4j 5.x with 5 node labels and 4 relationship types:
- **Nodes:**
  - `(:Paper {paper_id, doi, title, publication_year, citation_count, type, abstract})`
  - `(:Author {author_id, name, orcid})`
  - `(:Institution {institution_id, name, country_code, ror, type})`
  - `(:Venue {venue_id, name, type, issn, publisher})`
  - `(:Topic {topic_id, name, subfield, field, domain})`
- **Relationships:**
  - `(:Author)-[:AUTHORED {author_position, is_corresponding}]->(:Paper)`
  - `(:Author)-[:AFFILIATED_WITH {paper_id}]->(:Institution)`
  - `(:Paper)-[:PUBLISHED_IN]->(:Venue)`
  - `(:Paper)-[:HAS_TOPIC {score}]->(:Topic)`

### 4.2 Constraints & Performance Indexing
Formalized in `neo4j/schema.cypher`:
- **Uniqueness Constraints:** Ensure entity primary key uniqueness (`paper_id`, `author_id`, `institution_id`, `venue_id`, `topic_id`).
- **Indexes:**
  - Range indexes on `Paper(publication_year)` and `Paper(citation_count)` for temporal slicing and impact queries.
  - Point/B-tree indexes on `Author(name)`, `Author(orcid)`, `Institution(country_code)`.
  - Full-text search indexes on paper text (`title`, `abstract`) and entity names (`Author.name`, `Institution.name`).

---

## 5. Summary of Project-I Deliverables

| Deliverable | File Path | Status |
|---|---|---|
| **Raw Harvested Data** | `data/raw/openalex_raw_5000.json` | Completed |
| **Harvest Collection Log** | `data/raw/openalex_collection_log.json` | Completed |
| **Works Table** | `data/processed/works.csv` | Completed |
| **Authors Table** | `data/processed/authors.csv` | Completed |
| **Institutions Table** | `data/processed/institutions.csv` | Completed |
| **Venues Table** | `data/processed/venues.csv` | Completed |
| **Topics Table** | `data/processed/topics.csv` | Completed |
| **Authorship Edges** | `data/processed/authorships.csv` | Completed |
| **Affiliation Edges** | `data/processed/affiliations.csv` | Completed |
| **Work-Topic Edges** | `data/processed/work_topics.csv` | Completed |
| **Dataset Provenance & License** | `data/README.md` | Completed |
| **Data Dictionary** | `docs/data_dictionary.md` | Completed |
| **Graph Schema Specification** | `docs/graph_schema.md` | Completed |
| **Neo4j Constraints & Schema** | `neo4j/schema.cypher` | Completed |
| **Neo4j Loading Script** | `neo4j/load_data.cypher` | Completed |
| **Project-I Completion Report** | `docs/project_i_completion_report.md` | Completed |
