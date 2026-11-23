# Graph-Based Knowledge Graph for Research Collaboration Analysis
**Academic Project Title 34: Final Multi-Phase Implementation & Research Repository**

An end-to-end, reproducible framework for constructing, analyzing, and querying a heterogeneous scholarly Knowledge Graph and recommending future research collaborators. The project combines bibliographic entity extraction, Newman-weighted co-authorship networks, multi-resolution Louvain community detection, temporal collaboration dynamics, and a hybrid prospective collaborator recommender evaluated on a strict temporal split.

> **Provisional Scope Notice:**  
> The thematic focus on Artificial Intelligence and Machine Learning (OpenAlex Subfield `1702`: *Artificial Intelligence*), the temporal observation window (2016–2025 inclusive), and the 500-work-per-year impact-stratified sampling frame represent working research assumptions and design decisions, **not supervisor-approved constraints**. All documentation explicitly preserves this distinction.

---

## 1. Executive Overview & System Architecture

This repository contains the complete three-phase implementation of the academic project brief:

```
                            [OpenAlex Works API (Subfield 1702)]
                                            │
                                            ▼
                           data/raw/openalex_raw_5000.json
                                            │
                   ┌────────────────────────┴────────────────────────┐
                   ▼                                                 ▼
        [Relational Extraction]                            [Graph Model Schema]
       data/processed/*.csv                                neo4j/schema.cypher
       (Works, Authors, Insts,                             neo4j/load_data.cypher
        Venues, Topics, Edges)                             docker-compose.yml
                   │
                   ▼
     [Project-II: Graph Analytics]
       Newman Weighted Co-Authorship (N=22,037, E=221,903)
       GCC Extraction (14,879 nodes, 67.5% coverage)
       PageRank & Academic Brokerage (Betweenness)
       Louvain Communities (Q=0.9261 at γ=1.0)
       Temporal Dynamics (Team Size: 4.21 -> 9.42)
                   │
                   ▼
     [Project-III: Link Prediction & Recommender]
       Temporal Split: Train (2016–2021) vs. Test (2022–2025)
       Candidate Space: Strictly Non-Connected Researchers
       Hybrid Model (Adamic-Adar + Topic Cosine): MRR = 0.3379, Hits@10 = 61.5%
                   │
                   ▼
     [Interactive Prototype Dashboard]
       FastAPI Server (src/dashboard/app.py) @ http://127.0.0.1:8000
       Author Search, Ego-Network Inspection, Explainable Recommendations
```

---

## 2. Repository Structure & Key Deliverables

```
├── data/
│   ├── raw/
│   │   ├── openalex_raw_5000.json           # 5,000 raw API responses (500/year, 2016–2025)
│   │   └── openalex_collection_log.json     # Provenance, query params, pagination logs
│   ├── processed/
│   │   ├── works.csv                        # 4,989 unique works (11 duplicates removed)
│   │   ├── authors.csv                      # 22,185 unique authors (0 nulls; emails excluded)
│   │   ├── institutions.csv                 # 2,738 unique institutions with ROR & ISO country
│   │   ├── venues.csv                       # 904 publication venues (journals/conferences)
│   │   ├── topics.csv                       # 519 OpenAlex canonical research topics
│   │   ├── authorships.csv                  # 30,930 authorship edges (referential integrity: 100%)
│   │   ├── affiliations.csv                 # 33,410 affiliation edges
│   │   ├── work_topics.csv                  # 14,967 paper-topic classification edges
│   │   ├── coauthorship_edges.csv           # 221,903 Newman-weighted collaboration edges
│   │   ├── coauthorship_nodes.csv           # 22,037 active author nodes + isolated authors
│   │   ├── project_ii_results.json          # Network metrics, PageRank, Louvain communities
│   │   └── project_iii_recommendation_results.json # Link prediction evaluation metrics
│   ├── graph_ready/                         # Synced copies for Neo4j LOAD CSV import
│   └── README.md                            # Comprehensive data provenance & license notes
├── docker-compose.yml                       # Turnkey local Neo4j 5.x container with volume mount
├── docs/
│   ├── data_dictionary.md                   # Full metadata schema & data dictionary
│   ├── graph_schema.md                      # Node/relationship definitions & indexing strategy
│   ├── project_i_methodology.md             # Sampling frame, query design, audit results
│   ├── project_i_completion_report.md       # Project-I validation & quality sign-off
│   ├── project_ii_analysis_report.md        # Graph topology, Louvain calibration, temporal trends
│   ├── project_iii_recommendation_report.md # Recommendation evaluation & triadic closure analysis
│   ├── final_project_report.md              # Comprehensive academic thesis report
│   └── figures/                             # Publication-quality charts (PNG)
│       ├── fig1_degree_distribution.png     # Linear & log-log degree distribution
│       ├── fig2_community_sizes_and_topics.png # Top Louvain community sizes and topics
│       ├── fig3_temporal_collaboration_trends.png # 10-year team size & cross-institutional rates
│       └── fig4_top_centrality_researchers.png # PageRank vs. Strength comparison
├── literature_review.md                     # Literature review with verified primary citations
├── literature_matrix.csv                    # Structured comparison of scholarly KG literature
├── neo4j/
│   ├── schema.cypher                        # Node constraints, unique IDs, and B-tree indexes
│   ├── load_data.cypher                     # Idempotent LOAD CSV ingestion script
│   └── sample_queries.cypher                # Analytical Cypher queries for Neo4j Browser
├── src/
│   ├── harvest/
│   │   └── collect_openalex_corpus.py       # Deterministic, rate-limited OpenAlex harvester
│   ├── preprocess/
│   │   └── process_openalex_tables.py       # Relational normalizer & Newman weight generator
│   ├── audit/
│   │   └── audit_project_i_quality.py       # Integrity auditor (0 broken foreign keys)
│   ├── graph/
│   │   ├── build_coauthorship_graph.py      # NetworkX co-authorship projection builder
│   │   └── project_ii_network_analysis.py   # Topology, PageRank, Louvain, temporal trends
│   ├── recommendation/
│   │   └── collaborator_recommender.py      # Strict temporal split link prediction engine
│   └── dashboard/
│       ├── app.py                           # FastAPI interactive prototype dashboard
│       └── test_dashboard.py                # Automated endpoint test suite
├── RESEARCH_LOG.md                          # Timestamped log of decisions, sources, and audits
└── PROJECT_MASTER_PLAN.md                   # Three-phase project architecture roadmap
```

---

## 3. Quick Start & Execution Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.14.3 on Windows).
- Core dependencies: `networkx`, `scikit-learn`, `scipy`, `matplotlib`, `fastapi`, `uvicorn`, `requests`.

```bash
# Install required Python packages
pip install networkx scikit-learn scipy matplotlib fastapi uvicorn requests
```

---

### Step-by-Step Reproduction

#### Step 1: Verify Preprocessed Corpus & Referential Integrity (Project-I)
Run the automated quality and referential integrity audit script:
```bash
python src/audit/audit_project_i_quality.py
```
*Expected Output:* 100% referential integrity across all 7 relational tables (0 orphan edges, 0 null primary keys, 100% AI/ML topic relevance).

#### Step 2: Run Network Analysis & Community Detection (Project-II)
Compute global network topology, PageRank, betweenness centrality, Louvain communities at $\gamma \in \{0.5, 1.0, 1.5\}$, temporal collaboration trends, and generate figures:
```bash
python src/graph/project_ii_network_analysis.py
```
*Outputs generated:* `data/processed/project_ii_results.json` and 4 PNG figures in `docs/figures/`.

#### Step 3: Run Collaborator Recommendation Engine & Temporal Evaluation (Project-III)
Execute the link prediction engine under the strict temporal split (Train: 2016–2021 vs. Test: 2022–2025):
```bash
python src/recommendation/collaborator_recommender.py
```
*Outputs generated:* `data/processed/project_iii_recommendation_results.json`.

#### Step 4: Run the Local Interactive Prototype Dashboard
Launch the FastAPI dashboard to interactively search researchers, view ego-networks, and generate prospective recommendations:
```bash
python src/dashboard/app.py
```
Open your web browser and navigate to:
**`http://127.0.0.1:8000`**

To verify the dashboard test suite:
```bash
python src/dashboard/test_dashboard.py
```

---

### Step 5: Optional Local Neo4j Deployment
If Docker is installed on your local machine, start a dedicated Neo4j 5.x container with mounted data tables:
```bash
# Start Neo4j container in the background
docker compose up -d

# Wait ~15 seconds for Neo4j to initialize, then open Neo4j Browser at:
# http://localhost:7474 (Username: neo4j, Password: password123)

# In Neo4j Browser or cypher-shell, execute schema and load scripts:
# 1. Run neo4j/schema.cypher to create constraints and indexes
# 2. Run neo4j/load_data.cypher to import all entities and relationships
```
*Note:* The local analysis scripts (`src/graph/` and `src/recommendation/`) and prototype dashboard run completely independently using NetworkX and in-memory structures without requiring Neo4j to be active.

---

## 4. Key Empirical Findings

### 1. Network Topology & Small-World Structure (Project-II)
- **Scale:** 22,037 active researchers connected by 221,903 weighted co-authorship edges.
- **Macroscopic Connectivity:** A Giant Connected Component (GCC) spans **14,879 researchers (67.5% of the active network)**, resolving the extreme fragmentation observed in smaller pilot samples.
- **Transitivity:** Global clustering coefficient $C = 0.7726$, confirming dense triadic closure within research teams.
- **Louvain Modularity:** $Q = 0.9261$ at $\gamma = 1.0$ across 1,431 communities, cleanly delineating major subfields (NLP/LLMs, Deep RL, Computer Vision/Medical Imaging, Graph Neural Networks, and Speech Synthesis).

### 2. Temporal Collaboration Dynamics (2016–2025)
- **Team Size Expansion:** Mean co-author team size doubled over the decade, rising monotonically from **4.21 authors/paper in 2016** to **9.42 authors/paper in 2025**, driven by large-scale open-source and frontier LLM research consortia.
- **Cross-Institutional Integration:** Publications involving multiple independent institutions increased from **53.9% in 2016** to **72.8% in 2025**.

### 3. Prospective Collaborator Recommendation (Project-III)
Evaluated across 1,000 deterministic test queries against 100 negative candidate non-collaborators per query:
- **Topological Bottleneck:** Adamic-Adar achieves high top-1 precision (Hits@1: 17.2%), but reaches a hard ceiling at Hits@10 = 34.0% because **66.0% of future collaborators share no common mutual co-authors** ($d \ge 3$).
- **Semantic Generalization:** Topic Cosine similarity bridges disparate subgraphs, achieving Hits@10 = 58.1%.
- **Hybrid Superiority:** The Hybrid model combines local triadic structure with global topic alignment, achieving **MRR = 0.3379**, **Hits@1 = 21.0%**, and **Hits@10 = 61.5%** (+38.9% MRR gain over Adamic-Adar alone).

---

## 5. Primary Literature & Attribution

All literature references have been audited and verified against primary archival records:

1. **Newman, M. E. J. (2001).** *Scientific collaboration networks. II. Shortest paths, weighted networks, and centrality.* Physical Review E, 64(1), 016132. DOI: [10.1103/PhysRevE.64.016132](https://doi.org/10.1103/PhysRevE.64.016132).
2. **Newman, M. E. J. (2004).** *Coauthorship networks and patterns of scientific collaboration.* PNAS, 101(suppl_1), 5200–5205. DOI: [10.1073/pnas.0307545100](https://doi.org/10.1073/pnas.0307545100).
3. **Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008).** *Fast unfolding of communities in large networks.* Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008. DOI: [10.1088/1742-5468/2008/10/P10008](https://doi.org/10.1088/1742-5468/2008/10/P10008).
4. **Traag, V. A., Waltman, L., & van Eck, N. J. (2019).** *From Louvain to Leiden: guaranteeing well-connected communities.* Scientific Reports, 9(1), 5233. DOI: [10.1038/s41598-019-41695-z](https://doi.org/10.1038/s41598-019-41695-z).
5. **Wahle, J. P., Ruas, T., Mohammad, S. M., & Gipp, B. (2022).** *D3: A Massive Dataset of Scholarly Metadata for Analyzing the State of Computer Science Research.* In Proceedings of the 13th Language Resources and Evaluation Conference (LREC 2022), Marseille, France, pp. 2634–2642. arXiv: [2204.13384](https://arxiv.org/abs/2204.13384).
6. **Ferreira, A. A., Gonçalves, M. A., & Laender, A. H. (2012).** *A Brief Survey of Automatic Methods for Author Name Disambiguation.* ACM SIGMOD Record, 41(2), 15–26. DOI: [10.1145/2350036.2350040](https://doi.org/10.1145/2350036.2350040).
7. **Liben-Nowell, D., & Kleinberg, J. (2007).** *The link-prediction problem for social networks.* Journal of the American Society for Information Science and Technology, 58(7), 1019–1031. DOI: [10.1002/asi.20591](https://doi.org/10.1002/asi.20591).
8. **Priem, J., Piwowar, H., & Orr, R. (2022).** *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts.* arXiv preprint arXiv: [2205.01833](https://arxiv.org/abs/2205.01833).

---

## 6. License & Data Terms

- **Source Metadata:** Harvested from the official OpenAlex Works API. OpenAlex metadata is released worldwide into the public domain under the [Creative Commons CC0 1.0 Universal Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).
- **Privacy & Responsible Use:** Author email addresses have been strictly excluded from all tables, snapshots, and API responses. Canonical OpenAlex, ORCID, and ROR persistent identifiers are preserved throughout.
