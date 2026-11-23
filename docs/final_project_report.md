# Comprehensive Final Project Report
**Project Title 34: Graph-Based Knowledge Graph for Research Collaboration Analysis**  
*Academic Capstone / Master Project Synthesis*  
*Document Version:* 1.0.0 | *Status:* Completed & Validated | *Date:* November 2026  
*Provisional Scope Notice:* The AI/ML subfield (OpenAlex 1702) and 2016–2025 time window are working project assumptions, not supervisor-approved constraints.

---

## 1. Introduction & Academic Brief

The exponential expansion of scientific publication volume has made it increasingly challenging to systematically analyze cross-institutional research collaborations, track authoritative researchers, identify emerging disciplinary clusters, and discover prospective collaboration opportunities. Conventional bibliometric methods often treat co-authorship as unweighted binary links or aggregate metrics, obscuring the nuanced semantic relationships among authors, institutions, venues, and research topics.

This project delivers an end-to-end, reproducible framework across all three planned academic phases:
- **Project-I:** Bibliographic data acquisition, semantic preprocessing, entity linking, relational normalization, and graph database schema design.
- **Project-II:** Co-authorship projection with Newman collaboration weights, macroscopic network topology metrics, PageRank prestige, betweenness brokerage, multi-resolution Louvain community detection, and temporal collaboration dynamics.
- **Project-III:** Prospective collaborator recommendation evaluated on a strict temporal split (2016–2021 train vs. 2022–2025 test) with non-connected candidate constraints, and a lightweight, responsive local interactive dashboard runnable on a laptop.

---

## 2. Project-I: Corpus Acquisition, Quality Audit & Graph Schema

### 2.1 Thematic Scope & Data Harvesting
To overcome the severe domain dilution and temporal truncation identified during the pilot audit of the DBLP Discovery Dataset (which contained 52% non-AI false positives and ceased in 2021), we transitioned to the official **OpenAlex Works API**:
- **Disciplinary Filter:** Primary Topic Subfield `1702` (*Artificial Intelligence*), ensuring pure machine learning and AI coverage.
- **Temporal Range:** 2016–2025 inclusive (10 full calendar years).
- **Sampling Frame:** Deterministic year-stratified sampling harvesting 500 works per year ranked by global citation impact ($N = 5,000$ raw records).
- **License:** OpenAlex metadata is released globally into the public domain under Creative Commons CC0 1.0 Universal.
- **Privacy:** Author email addresses are strictly excluded; persistent identifiers (OpenAlex IDs, ORCID, ROR) are preserved.

### 2.2 Relational Entity Extraction & Referential Integrity
The raw harvest was normalized into 8 relational tables:
1. `works.csv`: 4,989 unique works (11 duplicate records resolved; 100% unique primary keys).
2. `authors.csv`: 22,185 unique authors (0 null IDs; 70.3% verified ORCIDs).
3. `institutions.csv`: 2,738 unique institutions with ROR URIs and ISO country codes.
4. `venues.csv`: 904 publishing venues (journals and conferences).
5. `topics.csv`: 519 canonical topics from the OpenAlex 2024 Topics taxonomy.
6. `authorships.csv`: 30,930 authorship edges.
7. `affiliations.csv`: 33,410 affiliation edges.
8. `work_topics.csv`: 14,967 work-topic classification edges.

An automated audit script (`src/audit/audit_project_i_quality.py`) confirmed **100.0% referential integrity** (0 broken foreign keys, 0 orphan relationships) and **100.0% AI/ML thematic relevance** across stratified random samples.

### 2.3 Graph Database Schema & Local Deployment
The graph schema models a heterogeneous scholarly network:
- **Node Labels:** `:Work`, `:Author`, `:Institution`, `:Venue`, `:Topic`.
- **Relationship Types:** `(:Author)-[:AUTHORED]->(:Work)`, `(:Work)-[:PUBLISHED_IN]->(:Venue)`, `(:Work)-[:HAS_TOPIC]->(:Topic)`, `(:Author)-[:AFFILIATED_WITH]->(:Institution)`.
- **Artifacts:** Full schema constraints (`neo4j/schema.cypher`), idempotent `LOAD CSV` commands (`neo4j/load_data.cypher`), and a turnkey `docker-compose.yml` for local Neo4j 5.x deployment.

---

## 3. Project-II: Network Topology, Centrality & Community Detection

### 3.1 Newman-Weighted Co-Authorship Projection
To account for hyper-collaborative publications, edge weights between authors $u$ and $v$ are formulated according to Newman (2001, 2004):
$$w_{uv} = \sum_{p \in P_u \cap P_v} \frac{1}{|A(p)| - 1}$$
where $|A(p)|$ represents the number of co-authors on paper $p$.

### 3.2 Macroscopic Network Topology
Analysis via `src/graph/project_ii_network_analysis.py` revealed:
- **Active Author Nodes ($|V|$):** 22,037 researchers (148 isolated authors with strictly single-author papers).
- **Weighted Edges ($|E|$):** 221,903 distinct collaboration partnerships.
- **Giant Connected Component (GCC):** 14,879 researchers (**67.5% of the active network**), with the second largest component containing only 155 nodes. This confirms the presence of an interconnected scientific core.
- **Average Degree:** 20.14 collaborators (Median: 8.0, Max: 467).
- **Global Transitivity:** $C = 0.7726$, reflecting realistic triadic closure and dense laboratory clustering.

### 3.3 Centrality Analysis & Academic Brokerage
- **PageRank ($\alpha = 0.85$):** Top prestigious researchers include **Luke Zettlemoyer** ($PR = 0.000672$), **Zhiyuan Liu** ($0.000596$), **Seyedali Mirjalili** ($0.000557$), **Quoc Viet Le** ($0.000534$), and **Philip S. Yu** ($0.000532$).
- **Academic Brokerage (Betweenness Centrality on GCC):** Evaluated via $k$-sampling ($k=200$). Top brokers bridging disparate subfields include **Alex Davies** ($BC = 0.1430$), **Demis Hassabis** ($0.1210$), **Samuel Albanie** ($0.1184$), **Arman Cohan** ($0.0919$), and **Greg S. Corrado** ($0.0894$).

### 3.4 Community Detection & Leiden vs. Louvain Calibration
We performed Louvain modularity optimization across three resolution parameters:
- $\gamma = 0.5$: Modularity $Q = 0.9215$ (1,413 macro-communities).
- $\gamma = 1.0$: Modularity $Q = 0.9261$ (1,431 communities) — optimal disciplinary boundary delineation.
- $\gamma = 1.5$: Modularity $Q = 0.9259$ (1,449 micro-communities).

*Algorithmic Note on Leiden:* While the Leiden algorithm (Traag et al., 2019) guarantees well-connected communities and eliminates Louvain's arbitrarily disconnected sub-clusters, `leidenalg` relies on C-extensions unavailable in the standard Windows sandbox without C++ compilers. Louvain with multi-resolution tuning serves as the validated runnable implementation.

Prominent communities identified at $\gamma = 1.0$ correspond directly to active research divisions:
1. **Community #01 (1,382 authors):** NLP, Large Language Models, Few-Shot Learning (Luke Zettlemoyer, Noah A. Smith, Hannaneh Hajishirzi).
2. **Community #05 (544 authors):** Robotics, Reinforcement Learning, Vision-Language (Sergey Levine, Pieter Abbeel, Trevor Darrell).
3. **Community #06 (511 authors):** Medical Image Analysis, Cancer Detection, Radiomics (Bram van Ginneken, Pheng-Ann Heng, Hao Chen).
4. **Community #07 (466 authors):** Deep Reinforcement Learning, Game AI, Scientific AI (David Silver, Demis Hassabis, Timothy Lillicrap).
5. **Community #09 (398 authors):** Graph Neural Networks, Data Mining (Philip S. Yu, Shirui Pan, Wenwu Zhu).

### 3.5 Temporal Collaboration Dynamics (2016–2025)
Respecting the 500-paper/year sampling design, structural collaborative indicators reveal:
- **Mean Team Size:** Rose monotonically from **4.21 authors/paper in 2016** to **9.42 authors/paper in 2025** (a 124% increase), reflecting the expansion of foundation model consortia.
- **Cross-Institutional Collaboration Rate:** Increased from **53.9% in 2016** to **72.8% in 2025**, indicating growing cross-organizational dependency on specialized compute infrastructure and diverse academic-industry expertise.

---

## 4. Project-III: Collaborator Recommendation & Rigorous Temporal Evaluation

### 4.1 Strict Temporal Experimental Setup
To guarantee zero data leakage:
- **Training Period (2016–2021):** 2,983 works used to construct historical graph $G_{\text{train}}$ ($|V_{\text{train}}| = 11,288$ authors, $|E_{\text{train}}| = 89,040$ edges) and author topic profiles.
- **Testing Period (2022–2025):** 1,998 works used to identify 3,326 ground-truth new collaborative edges formed between established researchers in $V_{\text{train}}$.
- **Candidate Pool Constraint:** For any query author $u$, candidate set $C(u)$ strictly excludes existing co-authors ($(u, v) \notin E_{\text{train}}$).

### 4.2 Candidate Ranking Results (101-Candidate Pool, N=1,000 Queries)

| Model | MRR | Hits@1 (%) | Hits@5 (%) | Hits@10 (%) | Precision@5 | Precision@10 | Recall@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Baseline** | 0.0519 | 1.0% | 5.0% | 9.9% | 0.0099 | 0.0099 | 0.0990 |
| **Jaccard Coefficient** | 0.2328 | 15.1% | 29.9% | 34.3% | 0.0598 | 0.0343 | 0.3430 |
| **Adamic-Adar Index** | 0.2433 | 17.2% | 30.0% | 34.0% | 0.0600 | 0.0340 | 0.3400 |
| **Topic Cosine Similarity** | 0.2569 | 11.8% | 41.7% | 58.1% | 0.0834 | 0.0581 | 0.5810 |
| **Hybrid (AA + Topic)** | **0.3379** | **21.0%** | **47.1%** | **61.5%** | **0.0942** | **0.0615** | **0.6150** |

### 4.3 Scientific Insight: Overcoming the Triadic Closure Bottleneck
- **Topological Limitation:** Pure topological methods (Adamic-Adar, Jaccard) exhibit high top-rank precision (Hits@1 = 17.2%) when candidates share mutual co-authors, but plateau at Hits@10 = 34.0%. **66.0% of all future collaborations in the test period occurred between authors who shared zero mutual collaborators in 2016–2021 ($d \ge 3$)**. Topological heuristics evaluate to 0.0 for all such pairs.
- **Content Generalization:** Topic Cosine similarity bridges disparate subgraphs by projecting authors into a continuous semantic topic space, achieving Hits@10 = 58.1%.
- **Hybrid Superiority:** The Hybrid model leverages structural proximity when mutual colleagues exist and falls back gracefully on topical alignment when bridging distant clusters, achieving an **MRR of 0.3379** and **Hits@10 of 61.5%** (+38.9% improvement over Adamic-Adar).

---

## 5. Local Interactive Prototype Architecture

The prototype dashboard (`src/dashboard/app.py`) is implemented using Python FastAPI with an embedded vanilla HTML5/Canvas user interface:
- **Zero External npm Dependencies:** Runs self-contained on any laptop via `python src/dashboard/app.py`.
- **Capabilities:**
  1. Instant researcher search and autocompletion across 22,185 authors.
  2. Complete research profile with institutional affiliations, historical publication catalog, and topic breakdown.
  3. Interactive ego-network listing direct co-authors with Newman collaboration weights.
  4. Live prospective collaborator recommendations displaying match score, topic alignment percentage, mutual intermediaries, and explainable rationale.
  5. Top Louvain community explorer.
- **Verification:** Fully validated via `src/dashboard/test_dashboard.py` (all 6 endpoint integration tests passing).

---

## 6. Threats to Validity & Limitations

1. **Impact-Stratified Sampling Frame:** The corpus consists of 500 top-cited papers per year. While this captures high-impact collaborative structures, it is not a uniform random sample of all published literature. Findings reflect trends among highly cited works rather than the long tail of low-citation publications.
2. **Author Name Disambiguation:** Author entities rely on OpenAlex's machine-learned author disambiguation models. While OpenAlex reports high precision, edge cases in common naming conventions remain possible.
3. **Leiden Implementation:** Modularity analysis relies on NetworkX's Louvain algorithm due to C++ compilation constraints on Windows. Leiden is documented as a theoretical benchmark.
4. **Provisional Scope:** Field AI/ML (Subfield 1702) and 2016–2025 window remain provisional working decisions subject to formal supervisor approval.

---

## 7. Deliverables & Artifact Verification Checklist

| Phase | Milestone Deliverable | File Path | Validation Status |
| :---: | :--- | :--- | :---: |
| **I** | Literature Review & Matrix | `literature_review.md`, `literature_matrix.csv` | **Completed** (Verified citations) |
| **I** | Raw Harvest & Collection Log | `data/raw/openalex_raw_5000.json`, `...log.json` | **Completed** (5,000 JSON records) |
| **I** | Clean Relational Tables (8 files)| `data/processed/*.csv`, `data/graph_ready/*.csv` | **Completed** (4,989 works, 22,185 authors) |
| **I** | Data Quality Audit Script | `src/audit/audit_project_i_quality.py` | **Completed** (100% integrity) |
| **I** | Neo4j Schema & Load Scripts | `neo4j/schema.cypher`, `neo4j/load_data.cypher` | **Completed** (Idempotent Cypher) |
| **I** | Local Neo4j Docker Compose | `docker-compose.yml` | **Completed** (Neo4j 5.x volume mounted) |
| **II** | Co-Authorship Graph Projection | `src/graph/build_coauthorship_graph.py` | **Completed** (221,903 weighted edges) |
| **II** | Graph Analytics & Communities | `src/graph/project_ii_network_analysis.py` | **Completed** (Q=0.9261, PageRank, Brokers) |
| **II** | Publication Figures (4 PNGs) | `docs/figures/fig1..4.png` | **Completed** (Degree, Comms, Trends, Centrality) |
| **II** | Project-II Analysis Report | `docs/project_ii_analysis_report.md` | **Completed** (Full analytical report) |
| **III**| Temporal Link Prediction Engine | `src/recommendation/collaborator_recommender.py`| **Completed** (MRR=0.3379, Hits@10=61.5%) |
| **III**| Project-III Evaluation Report | `docs/project_iii_recommendation_report.md` | **Completed** (Triadic closure analysis) |
| **III**| Interactive Local Dashboard | `src/dashboard/app.py` | **Completed** (FastAPI @ port 8000) |
| **III**| Dashboard Test Suite | `src/dashboard/test_dashboard.py` | **Completed** (6/6 tests passing) |
| **All**| Master User Guide | `README.md` | **Completed** (End-to-end instructions) |
| **All**| Timestamped Research Log | `RESEARCH_LOG.md` | **Completed** (Entries 1 through 11) |
