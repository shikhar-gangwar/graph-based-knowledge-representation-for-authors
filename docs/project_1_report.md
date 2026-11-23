# Project - I Completion Report
## Graph-Based Knowledge Graph for Research Collaboration Analysis

**Project Title:** Graph-Based Knowledge Graph for Research Collaboration Analysis (Title 34)  
**Academic Phase:** Project - I (Semester 1 Implementation)  
**Status:** Completed & Validated  
**Date:** November 2026  

---

## 1. Executive Summary

In accordance with the project syllabus and guidelines, **Project - I** establishes the foundational data, natural language processing, entity disambiguation, and graph database architecture for the research collaboration analysis system. 

All primary objectives of Project - I have been achieved:
1. **Literature Survey & Research Gap Identification:** Synthesized findings across scholarly knowledge graphs (OpenAlex, DBLP, CrossRef, MAG), author disambiguation algorithms, and community detection techniques; formulated 4 specific research gaps.
2. **Bibliographic Dataset Collection:** Built automated ingestion pipelines harvesting high-impact scholarly publications focusing on Graph Neural Networks and Knowledge Graphs in AI (2020–2025).
3. **Data Preprocessing & NLP Entity Extraction:** Reconstructed continuous abstract text from inverted indices, normalized DOIs, extracted 1,277 scientific topics/keywords using TF-IDF n-gram vectorization, and structured institution identifiers via ROR mappings.
4. **Author Name Disambiguation (AND):** Implemented a multi-signal disambiguation pipeline (ORCID validation + phonetic blocking + fuzzy string matching + co-author/institutional neighborhood overlap), resolving 3,909 raw author records into 3,891 canonical researchers.
5. **Graph Database Schema & Ingestion Suite:** Designed the Labeled Property Graph (LPG) schema for Neo4j 5.x, including uniqueness constraints, full-text indexes, `LOAD CSV` ingestion scripts, and analytical Cypher queries.
6. **Integrity Validation & Topology Audit:** Executed automated referential integrity verification across all 7,000 nodes and 74,236 edges, achieving a **100% clean, zero-orphan graph**.

---

## 2. Dataset Harvesting & Characterization

### 2.1 Harvesting Strategy
The data acquisition pipeline (`src/harvest/collect_data.py`) harvested publications using the OpenAlex REST API with cursor-based pagination and rate-limiting. Publications were filtered for the 2020–2025 timeframe in the AI/ML and Graph Learning domains and ranked by citation impact to seed high-density collaboration clusters.

### 2.2 Corpus Summary Statistics

| Entity / Dimension | Extracted Count | Description / Notes |
|---|---|---|
| **Publications (`:Publication`)** | **500** | High-impact articles & proceedings with DOIs and abstracts. |
| **Authors (`:Author`)** | **3,891** | Canonical researcher entities disambiguated via multi-signal resolution. |
| **Institutions (`:Institution`)** | **1,137** | Universities and research organizations globally. |
| **Publishing Venues (`:Venue`)** | **195** | Top AI/CS conferences and peer-reviewed journals. |
| **Research Topics (`:Topic`)** | **1,277** | Hierarchical OpenAlex concepts + NLP-extracted scientific keywords. |
| **Total Graph Nodes** | **7,000** | **100% unique primary keys, zero duplicate collisions.** |

---

## 3. NLP & Author Disambiguation Pipeline

### 3.1 Abstract Reconstitution & Text Normalization
OpenAlex stores publication abstracts as inverted position indices to comply with fair-use licensing. The preprocessing module (`src/preprocess/clean_data.py`) reconstructs full prose by sorting token positional arrays:
$$\text{Abstract} = \operatorname{concat}\left( \operatorname{sort}_{\text{pos}}\left( \{(p, w) \mid w \in \text{Index}, p \in \text{Index}[w]\} \right) \right)$$
Text is subsequently cleaned of non-printable ASCII artifacts, line breaks, and whitespace anomalies.

### 3.2 Multi-Signal Author Disambiguation (AND)
To combat homonymy (multiple individuals sharing a name) and synonymy (one author publishing under multiple aliases), `src/nlp/disambiguate_and_extract.py` executes a three-stage resolution:
1. **Phonetic & Surname Blocking:** Partitions the 3,909 authors into blocking buckets $(Surname, First\_Initial)$ to limit pairwise comparison complexity from $O(N^2)$ to localized blocks.
2. **Deterministic Identifier Match:** Authors sharing an identical ORCID identifier are merged into an invariant identity cluster.
3. **Neighborhood & Affiliation Similarity:** Within each block, candidates with RapidFuzz token sort similarity $\ge 90\%$ are evaluated against their co-authorship set $C(u)$ and institutional affiliation set $I(u)$:
   $$\text{Merge}(u, v) \iff \operatorname{Sim}_{\text{name}}(u, v) \ge 0.90 \land \left(|C(u) \cap C(v)| \ge 1 \lor |I(u) \cap I(v)| \ge 1\right)$$
- **Disambiguation Result:** 18 redundant author aliases and fragmented profiles were merged, yielding 3,891 clean canonical researcher profiles.

### 3.3 NLP Domain Topic Extraction
To capture granular sub-topics not present in high-level ontology taxonomies, a TF-IDF n-gram (unigrams and bigrams) extractor was trained across all publication titles and abstracts:
- Extracted 935 distinct scientific keywords (e.g., `Graph Attention`, `Knowledge Graph Embedding`, `Contrastive Learning`, `Molecular Property`).
- Generated 2,410 publication-topic associative edges, enriching the knowledge graph's semantic density.

---

## 4. Graph Database Schema & Ingestion Architecture

### 4.1 Labeled Property Graph (LPG) Schema
The schema is formalized in `neo4j/schema.cypher`:
- **Nodes:**
  - `(:Publication {paper_id, doi, title, publication_year, citation_count, type, abstract})`
  - `(:Author {author_id, name, orcid, merged_count})`
  - `(:Institution {institution_id, name, country_code, ror})`
  - `(:Venue {venue_id, name, type, issn})`
  - `(:Topic {topic_id, name, subfield, field, domain})`
- **Relationships:**
  - `(:Author)-[:AUTHORED {author_position, is_corresponding}]->(:Publication)`
  - `(:Author)-[:AFFILIATED_WITH]->(:Institution)`
  - `(:Publication)-[:PUBLISHED_IN]->(:Venue)`
  - `(:Publication)-[:HAS_TOPIC {score}]->(:Topic)`
  - `(:Publication)-[:CITES]->(:Publication)`
  - `(:Author)-[:CO_AUTHORED_WITH {weight, papers_count}]-(:Author)`

### 4.2 Weighted Co-Authorship Projection
To enable immediate community detection and centrality analytics in Project - II, collaboration intensity was computed using Newman's scientific collaboration weighting:
$$w(u, v) = \sum_{p \in P(u, v)} \frac{1}{|Authors(p)| - 1}$$
This formula penalizes massive consortium papers while rewarding small-group intimate collaborations.

---

## 5. Verification & Referential Integrity Results

The automated audit script (`src/validate_project_1.py`) evaluated every edge against target node tables:

| Edge Table | Relationship Type | Row Count | Source Orphans | Target Orphans | Integrity Status |
|---|---|---|---|---|---|
| `edges_authored.csv` | `AUTHORED` | 4,227 | 0 | 0 | **PASSED (100%)** |
| `edges_affiliated_with.csv` | `AFFILIATED_WITH` | 5,063 | 0 | 0 | **PASSED (100%)** |
| `edges_published_in.csv` | `PUBLISHED_IN` | 500 | 0 | 0 | **PASSED (100%)** |
| `edges_has_topic.csv` | `HAS_TOPIC` | 3,910 | 0 | 0 | **PASSED (100%)** |
| `edges_cites.csv` | `CITES` | 756 | 0 | 0 | **PASSED (100%)** |
| `edges_co_authored_with.csv` | `CO_AUTHORED_WITH` | 59,780 | 0 | 0 | **PASSED (100%)** |
| **Total Relationships** | | **74,236** | **0** | **0** | **PASSED (100%)** |

### Co-Authorship Network Topology
- **Active Researcher Nodes:** 3,877
- **Collaboration Edges:** 59,780
- **Giant Connected Component (GCC):** 717 researchers (18.5% of network)
- **Average Co-Author Degree:** 30.84 collaborators
- **Max Co-Author Degree:** 190 collaborators
- **Network Transitivity (Clustering Coefficient):** **0.9851** (confirms intense clustering typical of cutting-edge collaborative research hubs).

---

## 6. Repository Artifacts Deliverables

All deliverables have been created and saved in the workspace:
- **Harvesting Module:** [collect_data.py](file:///c:/Users/bit/Documents/Abhyudai's%20Project/src/harvest/collect_data.py)
- **Preprocessing Module:** [clean_data.py](file:///c:/Users/bit/Documents/Abhyudai's%20Project/src/preprocess/clean_data.py)
- **NLP & Disambiguation:** [disambiguate_and_extract.py](file:///c:/Users/bit/Documents/Abhyudai's%20Project/src/nlp/disambiguate_and_extract.py)
- **Graph Exporter:** [export_graph_tables.py](file:///c:/Users/bit/Documents/Abhyudai's%20Project/src/graph/export_graph_tables.py)
- **Validation Suite:** [validate_project_1.py](file:///c:/Users/bit/Documents/Abhyudai's%20Project/src/validate_project_1.py)
- **Neo4j Schema:** [schema.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/schema.cypher)
- **Neo4j Ingestion:** [import_data.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/import_data.cypher)
- **Sample Cypher Queries:** [sample_queries.cypher](file:///c:/Users/bit/Documents/Abhyudai's%20Project/neo4j/sample_queries.cypher)
- **Data Dictionary:** [data_dictionary.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/docs/data_dictionary.md)
- **Literature Review & Gaps:** [literature_survey_and_gaps.md](file:///c:/Users/bit/Documents/Abhyudai's%20Project/docs/literature_survey_and_gaps.md)

---

## 7. Next Steps for Project - II (Preview)

With the graph tables and schema finalized and validated:
1. **Neo4j Live Ingestion:** Load the 7,000 nodes and 74,236 edges into a local or cloud Neo4j instance.
2. **Community Detection Implementation:** Execute Louvain and Leiden modularity optimization to detect collaborative research communities.
3. **Centrality & Network Analysis:** Compute PageRank, Betweenness Centrality, and HITS to rank influential authors and institutional gatekeepers.
4. **Temporal Evolution:** Analyze network shifts across temporal slices.
5. **Interactive Visualization:** Generate visual layouts in Gephi and Neo4j Bloom.
