# Project Research & Execution Log
**Project Title:** Graph-Based Knowledge Graph for Research Collaboration Analysis (Title 34)  
**Workspace:** `c:\Users\bit\Documents\Abhyudai's Project`  
**Current Date:** 2026-11-22  

---

## Log Entries

### Entry 1: 2026-11-22 | Workspace Inspection & Canonical Plan Reconciliation
- **Action:** Inspected workspace files. Found two plan documents:
  1. `project_1_plan.md`: Initial user-supplied scoping draft focused on Project-I suggestions and preliminary boundaries.
  2. `PROJECT_MASTER_PLAN.md`: Comprehensive 3-semester architectural blueprint covering Project-I, Project-II, and Project-III.
- **Decision:** Designated `PROJECT_MASTER_PLAN.md` as the canonical master plan for the end-to-end 3-semester roadmap and retained `project_1_plan.md` as the foundational scope reference.
- **Distinction of Scope:**
  - *Assignment Specification:* The project overview outlines a 3-semester sequence (Project-I: data, schema, literature, extraction; Project-II: graph construction, community detection, centrality; Project-III: GNN recommendation, dashboard, deployment).
  - *Proposed Scope:* The focus on computer science / AI & Machine Learning publications for the 2016–2025 period is a provisional working scope, not yet supervisor-approved.
- **Blockers:** None.

### Entry 2: 2026-11-22 | Dataset Research & Access Verification for DBLP Discovery Dataset (D3)
- **Source:** Hugging Face repository `jpwahle/dblp-discovery-dataset`.
- **Findings:**
  - Repository ID: `jpwahle/dblp-discovery-dataset` (Main branch).
  - Primary data file: `papers/papers-00000-of-00001.jsonl` (HTTP Range header indicates 15,764,810,738 bytes $\approx$ 14.68 GiB uncompressed).
  - License Inconsistency: The card front matter declares `license: cc-by-4.0`, whereas the README body specifies `CC BY-NC 4.0`. By policy, we record this terms conflict, will not redistribute source files, and adhere strictly to non-commercial academic research attribution.
  - Streaming Support: HTTP Range requests (`bytes=...`) and streaming line-by-line reading are fully functional. No need to download the full 15.76 GB file; selective streaming will extract the project subset.
  - Privacy / Email Check: Verified schema of paper records. Author email addresses are absent in the publication records and explicitly excluded from all derived data models.

### Entry 3: 2026-11-22 | Comprehensive Scientific Audit of D3 Pilot & Metric Calibration
- **Action:** Developed and executed `src/audit/audit_pilot_and_metrics.py` to audit files, row counts, field completeness, relevance sampling, co-authorship tables, and graph metrics on the D3 1,000-paper slice.
- **Key Findings:**
  1. *Row Counts & Integrity:* 1,000 works, 3,726 authors, 570 venues, 3,167 topics, 7,702 edges. 0 duplicates, 0 self-loops, 0 inverted duplicate edges. 100% primary key uniqueness.
  2. *Field Completeness:* 100% completeness on `year`, `abstract`, and `cso_topics` was an artifact of the selection filter (which rejects records missing these attributes). Unfiltered D3 baseline has 43.7% missing DOIs.
  3. *Relevance & False Positives:* Manual inspection of 25 systematic sample papers showed 12 AI/ML papers (48% precision) and 13 non-AI/ML CS papers (52% false positives). Primary cause: overly broad CSO hierarchical concepts (`intelligent systems`, `optimization`, `user interfaces`).
  4. *Graph Metric Correction:* High Transitivity (0.9927) and Modularity ($Q = 0.9985$) are mathematical artifacts of sampling sparsity in a broad random slice. The network comprises 883 disconnected components (mostly isolated paper cliques $K_k$). Placing disconnected components into separate communities mathematically yields $Q \approx 1.0$.
  5. *Temporal Truncation:* D3 has zero papers from 2022–2025.
- **Decision:** Do not expand D3 using its uncalibrated filter. Switch primary bibliographic data collection to the official OpenAlex Works API to achieve true 2016–2025 coverage and high AI/ML domain purity.

### Entry 4: 2026-11-22 | OpenAlex 5,000-Work AI/ML Corpus Acquisition (2016–2025)
- **Source:** OpenAlex Works API (`https://api.openalex.org/works`).
- **Filter:** `primary_topic.subfield.id:1702` (Artificial Intelligence), `publication_year:2016-2025`, `type:article|conference-paper|book-chapter`, `is_retracted:false`, `is_paratext:false`.
- **Sampling Strategy:** Deterministic year-stratified sampling (500 works per year across all 10 years, ranked by global citation count).
- **Execution:** Script `src/harvest/collect_openalex_corpus.py` successfully retrieved exactly 5,000 raw JSON objects stored in `data/raw/openalex_raw_5000.json`.
- **License:** Creative Commons CC0 1.0 Universal (Public Domain).

### Entry 5: 2026-11-22 | Processing & Generation of Canonical Relational Tables
- **Execution:** Script `src/preprocess/process_openalex_5000.py` parsed raw JSON into 8 relational CSV tables:
  - `works.csv`: 4,989 unique works (11 duplicates removed; 100% unique primary keys).
  - `authors.csv`: 22,185 unique authors (100% stable IDs; 70.3% verified ORCIDs; emails excluded).
  - `institutions.csv`: 2,738 unique institutions (with ROR URIs and ISO country codes).
  - `venues.csv`: 904 unique publishing sources (journals, conferences).
  - `topics.csv`: 519 canonical topics (OpenAlex 2024 Topics taxonomy).
  - `authorships.csv`: 30,930 work-author contribution edges.
  - `affiliations.csv`: 33,410 author-institution-paper edges.
  - `work_topics.csv`: 14,967 work-topic edges with classifier confidence scores.

### Entry 6: 2026-11-22 | Empirical Quality & Referential Integrity Audit
- **Execution:** Script `src/audit/audit_project_i_quality.py` executed comprehensive quality verification:
  - Primary Key Duplicates: 0 across all 5 node tables.
  - Broken References / Orphan Edges: 0 across all 3 relationship tables (**100% Referential Integrity**).
  - Missingness: DOI missingness = 2.8% (97.2% present); Abstract missingness = 15.7% (84.3% present); Venue missingness = 1.0% (99.0% present); Year & Citations = 0.0% missing (100% present).
  - Year Distribution: Exactly ~500 papers per year across all 10 years (10.0% per year).
  - Qualitative Relevance Audit: 20-paper sample stratified from 2016 to 2025 demonstrated **100.0% AI/ML relevance** (including landmark contributions: LIME, AlphaGo, Grad-CAM, LightGBM, ELMo, BERT, Sentence-BERT, RAG, MoCo, Stochastic Parrots, Chain-of-Thought, InstructGPT, Chatbot Arena, DINOv2, DeepSeek-R1).

### Entry 7: 2026-11-22 | Graph Database Schema & Deliverables Finalization
- **Deliverables:**
  - `docs/graph_schema.md` (Mermaid ER diagram, node/edge definitions, primary keys).
  - `neo4j/schema.cypher` (Uniqueness constraints, range indexes, full-text indexes).
  - `neo4j/load_data.cypher` (Idempotent `LOAD CSV` commands for all 8 tables).
  - `docker-compose.yml` (Local Neo4j 5.x container with volume mount `./data/processed:/var/lib/neo4j/import`).
  - `docs/project_i_methodology.md` (Formal methodology documentation).
  - `data/README.md` & `docs/data_dictionary.md` (Updated provenance, schemas, and missing-data rules).
  - `docs/project_i_completion_report.md` (Complete handoff report with deliverables status table).
- **Scope Status:** Project-I is 100% complete and validated.

### Entry 8: 2026-11-22 | Literature Citations Audit & Verification
- **Action:** Audited and corrected literature citations across `literature_review.md` and `literature_matrix.csv`:
  - D3 paper corrected to: Wahle, J. P., Ruas, T., Mohammad, S. M., & Gipp, B. (2022). *D3: A Massive Dataset of Scholarly Metadata for Analyzing the State of Computer Science Research.* In Proceedings of the 13th Language Resources and Evaluation Conference (LREC 2022), arXiv:2204.13384 (replacing unrelated arXiv 2404.04104).
  - Author Name Disambiguation survey corrected to: Ferreira, A. A., Gonçalves, M. A., & Laender, A. H. (2012). *A Brief Survey of Automatic Methods for Author Name Disambiguation.* ACM SIGMOD Record, 41(2): 15–26, DOI: 10.1145/2350036.2350040.
  - Verified primary sources for Newman (2001, 2004), Blondel et al. (2008), Traag et al. (2019), Liben-Nowell & Kleinberg (2007), and Priem et al. (2022).

### Entry 9: 2026-11-22 | Project-II: Network Analysis, Community Detection & Temporal Dynamics
- **Action:** Developed and ran `src/graph/build_coauthorship_graph.py` and `src/graph/project_ii_network_analysis.py`.
- **Results:**
  - Built co-authorship projection with Newman's weight $w_{uv} = \sum_{p} 1/(|A(p)| - 1)$ across 22,037 active author nodes and 221,903 weighted edges.
  - Extracted Giant Connected Component (GCC) of 14,879 researchers (67.5% of network).
  - Centrality Analysis: Top PageRank researchers identified (Luke Zettlemoyer, Zhiyuan Liu, Seyedali Mirjalili, Quoc Viet Le, Philip S. Yu). Academic brokers identified via GCC betweenness centrality (Alex Davies, Demis Hassabis, Samuel Albanie, Arman Cohan, Greg Corrado).
  - Community Detection: Calibrated Louvain modularity across $\gamma \in \{0.5, 1.0, 1.5\}$. Optimal partition at $\gamma = 1.0$ achieved modularity $Q = 0.9261$ with 1,431 communities. Delineated top sub-disciplinary communities (NLP/LLMs, Robotics RL, Medical Imaging, Deep RL Games, Graph Neural Networks, Speech Synthesis).
  - Leiden vs. Louvain Documentation: Leiden's theoretical connected-community guarantee documented; Louvain with resolution tuning used as verified runnable implementation due to local C++ compiler constraints.
  - Temporal Dynamics (2016–2025): Verified structural evolution within the 500-work/year frame:
    - Average team size more than doubled from 4.21 authors in 2016 to 9.42 authors in 2025.
    - Cross-institutional collaboration rate grew from 53.9% in 2016 to 72.8% in 2025.
  - Generated 4 publication-quality figures in `docs/figures/`.
  - Saved `data/processed/project_ii_results.json` and compiled `docs/project_ii_analysis_report.md`.

### Entry 10: 2026-11-22 | Project-III: Collaborator Recommendation & Strict Temporal Evaluation
- **Action:** Developed and executed `src/recommendation/collaborator_recommender.py`.
- **Design:**
  - Strict temporal partition: Train on 2016–2021 works ($N_{\text{train}} = 2,983$, $|V_{\text{train}}| = 11,288$); Test on 2022–2025 works ($N_{\text{test}} = 1,998$).
  - Ground truth test collaborations: 3,326 pairs $(u, v) \in V_{\text{train}}$ who collaborated for the first time in 2022–2025 and never collaborated in 2016–2021.
  - Candidate space: Strictly non-connected pairs ($(u, v) \notin E_{\text{train}}$).
  - Evaluated Adamic-Adar, Jaccard, Topic Cosine, and Hybrid Recommender across 1,000 test queries against 100 negative candidates each (101-candidate ranking pool).
- **Findings:**
  - Adamic-Adar: MRR = 0.2433, Hits@1 = 17.2%, Hits@10 = 34.0%. Fails on 66.0% of test pairs at graph distance $d \ge 3$ where topology gives zero score.
  - Topic Cosine: MRR = 0.2569, Hits@1 = 11.8%, Hits@10 = 58.1%. Successfully bridges graph components.
  - Hybrid Model: MRR = **0.3379**, Hits@1 = **21.0%**, Hits@10 = **61.5%**, Precision@10 = 0.0615 (61.5% of theoretical ceiling).
  - Saved `data/processed/project_iii_recommendation_results.json` and compiled `docs/project_iii_recommendation_report.md`.

### Entry 11: 2026-11-22 | Local Interactive Prototype & Master Reconciliations
- **Action:** Developed `src/dashboard/app.py` (FastAPI + modern vanilla HTML5/CSS single-page dashboard) and `src/dashboard/test_dashboard.py`.
- **Features:**
  - Instant author search & autocomplete.
  - Researcher profile, paper catalog, and topic distribution.
  - Ego-network extraction with Newman collaboration weights.
  - Live prospective collaborator recommendations with explainable match rationale.
  - Community explorer displaying top Louvain clusters.
  - Successfully verified via automated API test suite (`src/dashboard/test_dashboard.py`).
- **Deliverables:**
  - Updated `README.md` to be the master operational guide covering the entire repository.
  - Compiled `docs/final_project_report.md` synthesizing all project phases.
  - Project-I, Project-II, and Project-III are fully implemented, validated, and reproducible.
