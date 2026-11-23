# Academic Literature Survey & Research Gap Analysis
## Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis

---

## 1. Introduction & Context

Scientific collaboration has become the primary mode of modern discovery. Interdisciplinary teams accelerate breakthroughs in critical domains, from deep learning and bio-computing to climate modeling. However, the sheer volume of publications—growing at over 8–9% annually—creates an information bottleneck. 

Analyzing research collaborations requires modeling complex social, institutional, and cognitive dynamics. This survey reviews existing approaches across three pillars:
1. **Scholarly Knowledge Graphs (SKGs) & Bibliographic Databases**
2. **Author Name Disambiguation (AND) in Scholarly Networks**
3. **Graph Analytics & Recommendation in Collaboration Networks**

---

## 2. Comparative Analysis of Scholarly Datasets & Knowledge Graphs

| Platform / Knowledge Graph | Scope & Coverage | Data Model | Open Access Level | Strengths | Limitations for Collaboration KG |
|---|---|---|---|---|---|
| **DBLP (Computer Science Bibliography)** | Computer Science (~7M publications, ~3.3M authors) | Relational / RDF Knowledge Graph | Fully Open (CC0 / ODC-By) | High data purity; curated conference proceedings; authority control. | Strictly CS domain; sparse abstract text; lacks institution normalization. |
| **OpenAlex** | Multidisciplinary (250M+ works, 100M+ authors) | Heterogeneous Entity Graph (LPG / JSON-LD) | Fully Open (CC0) | Comprehensive schema; integrated ROR institution IDs; concept hierarchy; open citations. | Automated harvesting introduces noise in author identity; rate-limits on massive dumps. |
| **Microsoft Academic Graph (MAG)** *(Deprecated 2021)* | Multidisciplinary (~260M works) | Entity-Relationship Model | Discontinued (Archived snapshots) | Historical benchmark for bibliometrics and citation networks. | Static, unmaintained since Dec 2021; superseded by OpenAlex. |
| **Semantic Scholar Open Research Corpus (S2ORC)** | Cross-domain (~136M papers, ~12M full text) | JSON Corpus & REST API | Open Academic API | Dense full-text parses; citation intents (background, method, result). | Strict API rate limits; author profile merges can lag behind OpenAlex. |
| **CrossRef** | All DOI-registered research (~150M items) | REST API / JSON | Open Metadata | Primary authoritative DOI registry; funder registry metadata. | Lacks native graph structure; sparse affiliation data for older works. |
| **Open Research Knowledge Graph (ORKG)** | Semantic research contributions | Semantic Web / RDF Ontologies | Open (CC-BY-SA) | Fine-grained semantic representation of scientific claims and hypotheses. | Limited coverage; requires manual crowd-curation; small scale for network analytics. |

---

## 3. Author Name Disambiguation (AND) Literature

Author Name Disambiguation is the task of resolving two primary entity resolution errors:
1. **Homonymy (Split Identity):** Different real-world researchers sharing identical or similar names (e.g., distinguishing between dozens of "Wei Wang" or "J. Smith" in computer science).
2. **Synonymy (Fragmented Identity):** A single researcher publishing under differing name variants (e.g., "Jure Leskovec", "J. Leskovec", "Jure M. Leskovec").

### 3.1 Taxonomy of AND Approaches
- **Rule-Based & Heuristic Methods:** Employ exact matching on persistent identifiers (ORCID, ResearcherID) and thresholding on string similarity (Jaro-Winkler, Levenshtein). Highly precise but fail when identifiers are absent (over 60% of legacy papers lack ORCIDs).
- **Graph-Based & Neighborhood Embedding:** Construct co-authorship ego-networks. Authors are grouped based on shared collaboration neighborhoods (Newman co-authorship overlap), citation coupling, and co-citation patterns.
- **Deep Learning & Graph Neural Networks:** Recent models (such as GCDAN, HGT-AND, and SciBERT-AND) encode multi-relational graphs combining paper text (abstract semantics), venues, co-authors, and institutions into a joint embedding space, followed by hierarchical agglomerative clustering (HAC).

---

## 4. Identified Research Gaps

Based on the critical review of existing scholarly frameworks, this project identifies four pivotal research gaps:

### Research Gap 1: Over-Reliance on Homogeneous Pairwise Projections
* **Current Limitation:** The vast majority of collaboration studies project multi-author papers into simple pairwise co-author graphs ($Author \leftrightarrow Author$).
* **Consequence:** This discards critical semantic context: what topics were investigated, which institutions facilitated the work, and which venues legitimized it. An author may collaborate with another researcher purely due to shared institutional computing resources rather than shared topical interest.
* **Proposed Gap Resolution:** Construct a **Heterogeneous Labeled Property Graph (LPG)** in Neo4j preserving explicit n-ary nodes: `Author`, `Publication`, `Institution`, `Topic`, and `Venue`.

### Research Gap 2: Inadequate Multi-Signal Disambiguation in Domain Subsets
* **Current Limitation:** Generic large-scale graph databases (like OpenAlex) often merge early-career researchers or split authors across changing institutional affiliations. Conversely, domain-specific subsets often lack automated disambiguation pipelines.
* **Proposed Gap Resolution:** Implement a localized multi-signal disambiguation engine combining ORCID anchoring, phonetic blocking, co-authorship neighborhood intersection, and affiliation verification.

### Research Gap 3: Static Snapshot Bias in Collaboration Analytics
* **Current Limitation:** Traditional bibliometric studies evaluate collaboration networks as static aggregates over a decade-long period.
* **Consequence:** Fails to capture the dynamic lifecycle of academic communities—how interdisciplinary bridges form, how subfields fracture, and how young researchers enter established communities.
* **Proposed Gap Resolution:** Model temporal network evolution using sliding temporal windows (2020–2025) and dynamic community detection (Leiden with temporal stability).

### Research Gap 4: Decoupling of Network Analytics and AI Recommendation
* **Current Limitation:** Existing tools either provide descriptive graph analytics (Gephi/VOSviewer) without predictive capabilities, or provide black-box deep learning link prediction without explainable graph interfaces.
* **Proposed Gap Resolution:** Bridge topological network analytics (PageRank, Betweenness) directly with predictive Graph Neural Networks (GraphSAGE/GAT) within an interactive dashboard that offers explainable match rationales.

---

## 5. Research Questions & Hypotheses

### Primary Research Question
*How can a heterogeneous, multi-entity knowledge graph improve the precision of research community discovery and the accuracy of prospective collaborator recommendation compared to conventional homogeneous co-authorship networks?*

### Sub-Questions
1. **RQ1 (Schema & Representation):** Does modeling institutions and NLP-derived topic nodes as explicit graph entities reduce community overlap error compared to co-author-only networks?
2. **RQ2 (Influence & Gatekeeping):** How do betweenness centrality and PageRank on a multi-relational knowledge graph differ from raw citation counts when identifying interdisciplinary academic brokers?
3. **RQ3 (Predictive Recommendation):** What is the gain in Link Prediction accuracy (ROC-AUC / Hits@10) when combining structural graph embeddings (Node2Vec) with semantic text embeddings (SciBERT) versus structural embeddings alone?

---

## 6. References
1. Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts.* arXiv preprint arXiv:2205.01833.
2. Ley, M. (2002). *The DBLP computer science bibliography: Evolution, research issues, perspectives.* SPIRE 2002, Springer, 1–10.
3. Newman, M. E. (2001). *Scientific collaboration networks. II. Shortest paths, weighted networks, and centrality.* Physical Review E, 64(1), 016132.
4. Traag, V. A., Waltman, L., & van Eck, N. J. (2019). *From Louvain to Leiden: guaranteeing well-connected communities.* Scientific Reports, 9(1), 5233.
5. Hamilton, W., Ying, Z., & Leskovec, J. (2017). *Inductive representation learning on large graphs (GraphSAGE).* NeurIPS 2017.
6. Beltagy, I., Lo, K., & Cohan, A. (2019). *SciBERT: A pretrained language model for scientific text.* EMNLP 2019.
