# Project - I Completion Report
## Graph-Based Knowledge Graph for Research Collaboration Analysis

**Project Title:** Graph-Based Knowledge Graph for Research Collaboration Analysis (Project Title 34)  
**Academic Phase:** Project - I (Complete Pass)  
**Status:** **100% Completed & Empirically Audited**  
**Execution Date:** 2026-11-22  
**Working Corpus Scope:** AI & Machine Learning Research (2016–2025 Inclusive)  
**Data Source:** OpenAlex Works API (Subfield 1702: Artificial Intelligence)  

---

## 1. Executive Summary & Deliverables Status

In accordance with the project syllabus, **Project - I** establishes the foundational literature review, bibliographic dataset acquisition, metadata preprocessing, entity linking, and graph database schema implementation. 

All Project-I requirements have been fulfilled without overstepping into Project-II (graph analytics, community detection) or Project-III (GNN link prediction, web application).

### Project-I Deliverables Status Table

| Deliverable | Expected Output / File | Status | Verification Evidence / Metric |
|---|---|---|---|
| **Literature Review** | [literature_review.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/literature_review.md) | **COMPLETE** | Verified against 8 primary peer-reviewed papers with DOIs. |
| **Literature Matrix** | [literature_matrix.csv](file:///c:/Users/bit/Documents/Abhyudai's%20Project/literature_matrix.csv) | **COMPLETE** | 7 structured columns: citation, goal, dataset, method, evaluation, findings, limitations. |
| **Raw Dataset Collection** | `data/raw/openalex_raw_5000.json` | **COMPLETE** | 5,000 raw JSON objects harvested across 10 years (2016–2025). |
| **Collection Audit Log** | `data/raw/openalex_collection_log.json` | **COMPLETE** | Verified 500 works per year quota across all 10 strata. |
| **Works Table** | `data/processed/works.csv` | **COMPLETE** | 4,989 unique works (11 duplicates removed; 100% unique primary keys). |
| **Authors Table** | `data/processed/authors.csv` | **COMPLETE** | 22,185 unique authors (100% stable IDs; emails excluded). |
| **Institutions Table** | `data/processed/institutions.csv` | **COMPLETE** | 2,738 unique institutions with country codes and ROR URIs. |
| **Venues Table** | `data/processed/venues.csv` | **COMPLETE** | 904 unique publishing sources (journals, conferences) with ISSNs. |
| **Topics Table** | `data/processed/topics.csv` | **COMPLETE** | 519 canonical topics within OpenAlex Topics 2024 Taxonomy. |
| **Authorship Edges** | `data/processed/authorships.csv` | **COMPLETE** | 30,930 edges; 0 broken references; position & corresponding flags. |
| **Affiliation Edges** | `data/processed/affiliations.csv` | **COMPLETE** | 33,410 edges linking author, institution, and paper context; 0 broken references. |
| **Work-Topic Edges** | `data/processed/work_topics.csv` | **COMPLETE** | 14,967 edges with classifier confidence scores; 0 broken references. |
| **Dataset Provenance** | [data/README.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/data/README.md) | **COMPLETE** | Detailed query parameters, license (CC0), scope, and row counts. |
| **Data Dictionary** | [docs/data_dictionary.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/docs/data_dictionary.md) | **COMPLETE** | Complete field definitions, data types, constraints, and missing-data rules. |
| **Graph Schema Specification** | [docs/graph_schema.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/docs/graph_schema.md) | **COMPLETE** | Mermaid ER diagram, node/edge definitions, primary keys, and design rationale. |
| **Neo4j Constraints & Schema** | [neo4j/schema.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/schema.cypher) | **COMPLETE** | Idempotent uniqueness constraints, range indexes, and full-text indexes. |
| **Neo4j Ingestion Script** | [neo4j/load_data.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/load_data.cypher) | **COMPLETE** | Idempotent `LOAD CSV` commands for all 5 node and 3 relationship tables. |
| **Project-I Methodology** | [docs/project_i_methodology.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/docs/project_i_methodology.md) | **COMPLETE** | Formal documentation of harvesting, preprocessing, entity extraction, and schema. |
| **Research Execution Log** | [RESEARCH_LOG.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/RESEARCH_LOG.md) | **COMPLETE** | Date-stamped chronological audit of decisions, actions, and findings. |

---

## 2. Dataset Provenance, Scope & License

- **Source API:** OpenAlex Works API (`https://api.openalex.org/works`)
- **Query Filter:** `primary_topic.subfield.id:1702` (Artificial Intelligence), `publication_year:2016-2025`, `type:article|conference-paper|book-chapter`, `is_retracted:false`, `is_paratext:false`.
- **Sampling Strategy:** Deterministic year-stratified sampling (500 works per year across 10 years, ranked by global citation count).
- **Retrieval Date:** 2026-11-22
- **Data License:** Creative Commons CC0 1.0 Universal (Public Domain).
- **Scope Status:** **Provisional working scope**, chosen for high relevance and historical balance; not yet supervisor-approved.

---

## 3. Preprocessing & Entity Resolution Rules

1. **Deduplication:** Raw records deduplicated by stable OpenAlex Work ID (`W...`) and normalized DOI (lowercase, URL prefix stripped). 11 duplicates were detected and removed, leaving 4,989 unique works.
2. **Abstract Reconstitution:** Reconstructed from OpenAlex `abstract_inverted_index` by sorting token arrays by word position. Missing abstracts are preserved as empty strings; no synthetic text was fabricated.
3. **Author Identity Resolution:** Authors mapped to persistent OpenAlex Author IDs (`A...`) and verified ORCIDs. Authors lacking source IDs were assigned deterministic fallback IDs (`A_anon_{hash(name + work_id)}`). **Authors were never merged by name string alone.**
4. **Privacy:** Author email addresses are completely excluded.
5. **Institutional Authority Control:** Institutions resolved via canonical OpenAlex IDs (`I...`), capturing official ROR URIs and ISO country codes.

---

## 4. Empirical Data Quality & Verification Checks

The automated quality verification script (`src/audit/audit_project_i_quality.py`) audited all processed tables:

### 4.1 Missingness Rates (N=4,989 Works)
- **Publication Year:** 0 missing (100.0% present)
- **Citation Count:** 0 missing (100.0% present)
- **Publishing Venue ID:** 52 missing (99.0% present | 1.0% missing)
- **DOI:** 138 missing (97.2% present | 2.8% missing)
- **Abstract:** 782 missing (84.3% present | 15.7% missing)

### 4.2 Author Attributes (N=22,185 Authors)
- **Author ID & Name:** 100.0% present (0 missing)
- **Verified ORCID:** 15,607 present (70.3% present | 29.7% missing)

### 4.3 Publication Year Distribution (2016–2025)
- 2016: 497 papers (10.0%)
- 2017: 499 papers (10.0%)
- 2018: 500 papers (10.0%)
- 2019: 497 papers (10.0%)
- 2020: 497 papers (10.0%)
- 2021: 499 papers (10.0%)
- 2022: 500 papers (10.0%)
- 2023: 500 papers (10.0%)
- 2024: 500 papers (10.0%)
- 2025: 500 papers (10.0%)
- *Result:* Perfect year balance across the entire decade.

### 4.4 Referential Integrity Audit
- `authorships.csv`: 0 broken `paper_id` references, 0 broken `author_id` references (**PASSED**).
- `affiliations.csv`: 0 broken `author_id`, 0 broken `institution_id`, 0 broken `paper_id` references (**PASSED**).
- `work_topics.csv`: 0 broken `paper_id`, 0 broken `topic_id` references (**PASSED**).
- `works.csv` venue links: 0 broken `venue_id` references (**PASSED**).
- **Result: 100% Referential Integrity (Zero Orphan Edges).**

### 4.5 Qualitative Relevance Audit (Stratified Sample of 20 Papers)
A sample of 2 papers per year across all 10 years was manually inspected:
- **Sample AI/ML Precision:** **100.0% (20/20 relevant)**.
- Sample includes seminal contributions: *LIME* (2016), *AlphaGo* (2016), *Grad-CAM* (2017), *LightGBM* (2017), *ELMo* (2018), *BERT* (2019), *Sentence-BERT* (2019), *RAG* (2020), *MoCo* (2020), *Stochastic Parrots* (2021), *Chain-of-Thought Prompting* (2022), *InstructGPT* (2022), *Chatbot Arena* (2023), *DINOv2* (2024), *DeepSeek-R1* (2025).
- Eliminates the 52% false-positive noise observed in the D3 audit.

---

## 5. Graph Schema & Ingestion Blueprint

### 5.1 LPG Schema Summary
- **Nodes:**
  - `(:Paper {paper_id, doi, title, publication_year, citation_count, type, abstract})`
  - `(:Author {author_id, name, orcid})`
  - `(:Institution {institution_id, name, country_code, ror, type})`
  - `(:Venue {venue_id, name, type, issn, publisher})`
  - `(:Topic {topic_id, name, subfield, field, domain})`
- **Edges:**
  - `(:Author)-[:AUTHORED {author_position, is_corresponding}]->(:Paper)`
  - `(:Author)-[:AFFILIATED_WITH {paper_id}]->(:Institution)`
  - `(:Paper)-[:PUBLISHED_IN]->(:Venue)`
  - `(:Paper)-[:HAS_TOPIC {score}]->(:Topic)`

### 5.2 How to Load the Knowledge Graph in Neo4j
1. Copy all CSV files from `data/processed/` to your Neo4j database `import/` directory.
2. Open Neo4j Browser or `cypher-shell`.
3. Execute [neo4j/schema.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/schema.cypher) to create uniqueness constraints and search indexes.
4. Execute [neo4j/load_data.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/load_data.cypher) to ingest all nodes and edges via parameterized `LOAD CSV` commands.

---

## 6. Assumptions & Limitations Needing Supervisor Confirmation

1. **Domain Boundary:** The corpus focuses on AI and Machine Learning research (`subfield 1702`). If the supervisor prefers a broader computer science scope or a different specialized subfield (e.g., Computer Vision alone, Bioinformatics, or Cyber-Physical Systems), the query filter parameter can be adjusted.
2. **Corpus Size:** 4,989 works (22,185 authors, 2,738 institutions) is suitable for rapid, memory-efficient graph algorithm execution in Project-II. Confirm if the supervisor prefers scaling to 15,000–30,000 works.
3. **Temporal Window:** 2016–2025 provides an even 10-year decade. Confirm whether older foundational literature (pre-2016) is required.

---

## 7. Next Steps for Project - II

With the Project-I foundation completed and validated:
1. **Neo4j Graph Instantiation:** Load the 4,989 papers, 22,185 authors, 2,738 institutions, 904 venues, and 519 topics into a live Neo4j 5.x instance.
2. **Co-Authorship Projection:** Generate weighted co-authorship projections using Newman's scientific collaboration weighting.
3. **Centrality Analysis:** Execute PageRank, Betweenness Centrality, and Degree Centrality in Neo4j GDS to identify key academic brokers and institutional hubs.
4. **Community Detection:** Implement the Leiden and Louvain algorithms to identify research communities and evaluate partition modularity ($Q$) on the Giant Connected Component.
5. **Interactive Visualization:** Export subgraphs for high-resolution rendering in Gephi and configure Neo4j Bloom exploration styles.
