# Final Report & Defense Presentation Outline
## Graph-Based Knowledge Graph for Research Collaboration Analysis

---

## Part A: Final Report Structure (Thesis / Semester Submission)

### 1. Title Page & Abstract
- **Project Title:** Graph-Based Knowledge Graph for Research Collaboration Analysis
- **Abstract:** Problem overview, multi-entity knowledge graph rationale, dataset provenance (DBLP Discovery Dataset D3), methodology (Newman weighting, Louvain/Leiden modularity, PageRank), empirical network findings ($Q = 0.9985$, Transitivity $= 0.9927$), and roadmaps for AI collaborator recommendation.

### 2. Introduction & Motivation
- Exponential growth of scientific literature and the collapse of manual tracking.
- The limitation of homogeneous co-authorship networks: loss of topical, institutional, and venue context.
- Objectives across the three-semester curriculum.
- Distinguishing assignment requirements vs. empirical literature findings vs. provisional working scope (Computer Science AI/ML 2016–2025).

### 3. Literature Review & Related Work
- Systematic comparison of Scholarly Knowledge Graphs (DBLP, OpenAlex, S2ORC, MAG).
- Author Name Disambiguation (AND) paradigms: heuristic, graph neighborhood, and transformer embeddings.
- Community detection algorithms: from Louvain to Leiden; modularity vs. Constant Potts Model (CPM).
- Academic collaborator recommendation: topological heuristics, meta-path random walks, and Graph Neural Networks (GraphSAGE, GAT).
- 4 Formal Research Gaps and refined Research Questions.

### 4. Dataset Acquisition & Methodology
- The DBLP Discovery Dataset (D3) by Wahle et al. (LREC-COLING 2024).
- Source availability, size (15.76 GB), and HTTP streaming architecture.
- License analysis & resolution (CC BY 4.0 metadata vs. CC BY-NC 4.0 terms).
- Exclusion of author email addresses and privacy adherence.
- Inclusion rules: Computer Science taxonomy + Computer Science Ontology (CSO) concepts + keyword verification.
- Pilot dataset audit (N=100) and missingness metrics; analysis of false positives in cross-domain applications.
- Corpus expansion: 1,000 publications, 3,726 authors, 570 venues, 3,167 topics.

### 5. Knowledge Graph Schema & Ingestion Architecture
- Labeled Property Graph (LPG) design in Neo4j.
- Nodes: `Paper`, `Author`, `Venue`, `Topic` (and optional `Institution`).
- Edges: `AUTHORED`, `PUBLISHED_IN`, `HAS_TOPIC`, and weighted `CO_AUTHORED_WITH`.
- Newman's scientific collaboration weighting formulation:
  $$w(u, v) = \sum_{p \in P(u, v)} \frac{1}{|Authors(p)| - 1}$$
- Constraints, range indexes, and full-text Cypher search indexes.
- Idempotent `LOAD CSV` execution.

### 6. Network Analytics & Community Detection Findings
- Network topology metrics: node count, degree distribution, connected components, density, transitivity.
- Centrality ranking: PageRank on the Giant Connected Component (GCC) vs. raw citation volume.
- Louvain community detection results: partition modularity ($Q = 0.9985$).
- Qualitative community profiling: mapping the top 5 largest communities to prominent researchers and core CSO topics (Computer Vision, NLP, Distributed Systems, Big Data).

### 7. Future Work (Project-II and Project-III Roadmap)
- Implementation of the Leiden algorithm for guaranteed connected community partitions.
- Machine Learning & GNN link prediction for collaborator recommendation (treating this strictly as a future stretch goal evaluated on temporal splits).
- Web-based interactive exploration dashboard and Neo4j Bloom styles.

### 8. Threats to Validity & Limitations
- License restrictions preventing raw redistribution.
- Absence of fine-grained institutional affiliation for historical DBLP records.
- Inherent sampling bias in keyword-based domain subsetting.

### 9. References & Appendices
- Full bibliographic citations.
- Data dictionary and reproducible code repository.

---

## Part B: Defense Presentation Slide Deck Outline (15–20 Minutes)

| Slide # | Slide Title | Visual & Content Elements |
|---|---|---|
| **Slide 1** | **Title Slide** | Project Title, Student Name, Roll/Reg Number, Supervisor Name, Academic Year. |
| **Slide 2** | **The Research Problem** | "Information overload in scientific publishing"; side-by-side comparison: *Pairwise co-authorship graph (loss of semantics)* vs. *Heterogeneous Knowledge Graph (rich context)*. |
| **Slide 3** | **Project Scope & 3-Semester Roadmap** | Highlighting Project-I (Data, Schema, Extraction) as completed, and Project-II / Project-III as planned next phases. |
| **Slide 4** | **Literature Survey & The 4 Gaps** | Literature matrix summary: Semantic loss, community disconnectedness, temporal leakage, and black-box recommendations. |
| **Slide 5** | **Data Acquisition: DBLP Discovery Dataset (D3)** | Hugging Face streaming architecture; avoiding full 15.76 GB download; license reconciliation (CC BY-NC 4.0 academic use); zero email exposure. |
| **Slide 6** | **Pilot Validation (N=100) & Missingness** | Bar charts showing 100% abstract, title, and authorId completeness; qualitative analysis of false positives in cross-disciplinary topics. |
| **Slide 7** | **The Working Knowledge Graph Schema** | Mermaid / visual LPG diagram: `Paper`, `Author`, `Venue`, `Topic`; relationship cardinalities. |
| **Slide 8** | **Network Topology Findings** | Metrics table: 3,650 active authors, 7,702 weighted edges, Transitivity $= 0.9927$ (intense team clustering). |
| **Slide 9** | **Community Detection Results** | Louvain modularity $Q = 0.9985$; pie chart of community distribution; callout boxes for top 3 communities (AI/CV, Distributed Systems, Big Data). |
| **Slide 10** | **Influential Researcher Centrality** | PageRank vs. Degree Centrality leaderboard on the Giant Connected Component. |
| **Slide 11** | **Neo4j Implementation & Queries** | Screenshot / Cypher demo: multi-hop author-to-topic exploration and ego-network traversal. |
| **Slide 12** | **Project-II & Project-III Next Steps** | Timeline for Leiden algorithm comparison, GNN prospective link prediction, and interactive web dashboard. |
| **Slide 13** | **Summary & Contributions** | Reproducible research package, clean dataset tables, verified schema, zero synthetic data. |
| **Slide 14** | **Q&A / References** | Acknowledgments, primary paper links, open for questions. |
