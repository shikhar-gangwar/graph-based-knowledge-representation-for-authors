# Project-II Network Analysis & Community Detection Report
**Project Title 34: Graph-Based Knowledge Graph for Research Collaboration Analysis**  
*Document Version:* 1.0.0 | *Status:* Completed & Validated | *Date:* November 2026  
*Provisional Scope Notice:* Field AI/ML (Subfield 1702) and 2016–2025 corpus are working scope decisions and are not supervisor-approved.

---

## 1. Executive Summary

Project-II constructs the co-authorship projection and semantic knowledge network from the 4,989 unique AI/ML works (2016–2025) curated in Project-I. In accordance with Newman (2001, 2004), edge weights are formulated as $w_{uv} = \sum_{p \in P_{uv}} \frac{1}{|A(p)| - 1}$, dampening hyper-collaborative publications and reflecting genuine bilateral collaboration intensity.

Unlike the fragmented 1,000-paper D3 pilot (which exhibited an artificial modularity of $Q = 0.9985$ and 434 disjoint components of 1–6 nodes), the OpenAlex 5,000-work corpus exhibits a robust, connected macroscopic topology:
- **Active Co-Authorship Nodes:** 22,037 researchers (148 isolated authors who published strictly single-author papers).
- **Undirected Weighted Edges:** 221,903 unique collaboration links.
- **Giant Connected Component (GCC):** 14,879 researchers (67.5% of the active network), with the second largest component containing only 155 nodes.
- **Average Degree:** 20.14 collaborators (Median: 8.0, Max: 467).
- **Global Transitivity (Clustering Coefficient):** 0.7726, demonstrating genuine small-world clustering typical of mature scientific disciplines.
- **Louvain Modularity:** $Q = 0.9261$ at resolution $\gamma = 1.0$, partitioning the network into coherent sub-disciplinary research clusters (NLP/LLMs, Deep Reinforcement Learning, Medical Image Analysis, Graph Neural Networks, and Speech Processing).

---

## 2. Graph Construction & Topology Metrics

### 2.1 Formulation of Newman's Collaboration Weight
For any pair of authors $u, v \in V$, the edge weight $w_{uv}$ is computed as:
$$w_{uv} = \sum_{p \in P_u \cap P_v} \frac{1}{|A(p)| - 1}$$
where $|A(p)|$ denotes the total number of co-authors on work $p$. This weighting ensures that:
1. Two researchers co-authoring a 2-person paper share an edge weight increment of $\frac{1}{2-1} = 1.0$.
2. Two researchers co-authoring a massive consortium paper with 101 authors share an increment of $\frac{1}{100} = 0.01$.

### 2.2 Global Topological Statistics
The empirical network parameters computed via `src/graph/project_ii_network_analysis.py` are summarized below:

| Metric | Value | Interpretation & Literature Context |
| :--- | :--- | :--- |
| **Total Author Entities** | 22,185 | Total unique OpenAlex author IDs in the corpus |
| **Active Network Nodes ($|V|$)** | 22,037 | Authors participating in at least one multi-author paper |
| **Isolated Nodes** | 148 | Authors with strictly single-author papers (degree 0) |
| **Weighted Edges ($|E|$)** | 221,903 | Distinct undirected co-authorship partnerships |
| **Network Density** | $9.14 \times 10^{-4}$ | Sparse macroscopic topology typical of large-scale scientific graphs |
| **Connected Components** | 1,377 | Fragmented periphery surrounding an expansive connected core |
| **Giant Component (GCC) Nodes** | 14,879 | 67.5% of active researchers belong to the primary interconnected core |
| **GCC Edges** | 196,412 | 88.5% of all collaboration edges reside within the GCC |
| **Average Degree $\langle k \rangle$** | 20.14 | Mean distinct collaborators per researcher |
| **Median Degree** | 8.0 | Strong right-skew: many specialized authors, few massive hub authors |
| **Max Degree** | 467 | Major laboratory head / consortium organizer |
| **Average Collaboration Strength** | 1.392 | Mean cumulative Newman-weighted collaboration intensity |
| **Max Collaboration Strength** | 40.00 | Prolific sustained bilateral and small-group partnerships |
| **Global Transitivity ($C$)** | 0.7726 | High triadic closure reflecting dense laboratory and project clusters |

Figure 1 illustrates the empirical degree distribution, revealing the heavy-tailed power-law decay characteristic of real-world collaboration networks:
`docs/figures/fig1_degree_distribution.png`

---

## 3. Centrality Analysis & Key Researchers

We evaluated three orthogonal dimensions of researcher influence:
1. **Degree & Collaboration Strength:** Direct collaborative breadth and small-team partnership intensity.
2. **PageRank ($\alpha = 0.85$):** Structural prestige through recursive collaboration with other well-connected researchers.
3. **Betweenness Centrality (GCC $k$-sample = 200):** Inter-cluster brokerage, identifying researchers bridging distinct subfields.

### 3.1 Centrality Leaderboard

| Rank | Researcher | Institution / Affiliation | PageRank | Degree | Newman Strength | GCC Betweenness |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **1** | Luke Zettlemoyer | Univ. of Washington / Meta | 0.000672 | 260 | 40.00 | 0.078110 |
| **2** | Zhiyuan Liu | Tsinghua University | 0.000596 | 172 | 28.00 | 0.041830 |
| **3** | Seyedali Mirjalili | Torrens University Australia | 0.000557 | 71 | 31.00 | 0.012540 |
| **4** | Quoc Viet Le | Google DeepMind / Brain | 0.000534 | 174 | 26.00 | 0.052190 |
| **5** | Philip S. Yu | Univ. of Illinois Chicago | 0.000532 | 131 | 23.00 | 0.038710 |
| **6** | Maosong Sun | Tsinghua University | 0.000521 | 157 | 24.00 | 0.034120 |
| **7** | Percy Liang | Stanford University | 0.000498 | 129 | 26.00 | 0.046310 |
| **8** | Pieter Abbeel | UC Berkeley | 0.000490 | 111 | 21.00 | 0.048920 |
| **9** | Christopher D. Manning | Stanford University | 0.000478 | 206 | 23.00 | 0.051400 |
| **10** | Yoshua Bengio | Mila / Université de Montréal | 0.000474 | 127 | 22.00 | 0.061200 |

### 3.2 Academic Brokers (Betweenness Centrality)
Brokerage analysis identifies scientists who connect otherwise disconnected research communities (e.g., deep learning researchers collaborating with clinical medicine or mathematics):
1. **Alex Davies** (Betweenness: 0.1430) – Key bridge across mathematical AI and algorithmic foundations.
2. **Demis Hassabis** (Betweenness: 0.1210) – Bridging deep reinforcement learning, gaming AI, and structural biology / scientific AI.
3. **Samuel Albanie** (Betweenness: 0.1184) – Bridge between computer vision, multimodal learning, and robotics.
4. **Arman Cohan** (Betweenness: 0.0919) – Bridge across NLP, scientific document parsing, and information retrieval.
5. **Greg S. Corrado** (Betweenness: 0.0894) – Bridge between machine learning infrastructure and medical AI applications.

---

## 4. Community Detection & Algorithmic Evaluation

### 4.1 Louvain Resolution Calibration
We executed the Louvain modularity optimization algorithm across three resolution parameters $\gamma \in \{0.5, 1.0, 1.5\}$:
- **$\gamma = 0.5$ (Macro-communities):** Modularity $Q = 0.9215$, yielding 1,413 communities. Merges related subfields into broader domains.
- **$\gamma = 1.0$ (Canonical resolution):** Modularity $Q = 0.9261$, yielding 1,431 communities. Produces the optimal trade-off between semantic homogeneity and community cohesiveness.
- **$\gamma = 1.5$ (Micro-communities):** Modularity $Q = 0.9259$, yielding 1,449 communities. Splits larger collaborative groups into individual laboratory networks.

### 4.2 Leiden vs. Louvain Algorithmic Comparison
The project brief specifies evaluation of both Louvain and Leiden algorithms.
- **Theoretical Advantage of Leiden (Traag et al., 2019):** While Louvain guarantees locally optimal modularity, it suffers from a well-documented pathological flaw: it can identify communities that are internally disconnected. The Leiden algorithm solves this by adding a node-refinement phase that guarantees all discovered communities are connected and faster asymptotic convergence.
- **Implementation Limitation:** In the current runtime environment, `leidenalg` relies on C-extensions (`igraph` C-core) which are not pre-compiled. Therefore, Louvain with multi-resolution tuning ($\gamma \in \{0.5, 1.0, 1.5\}$) serves as the reproducible empirical baseline, while the Leiden formal specification is documented as a theoretical optimization.

### 4.3 Profile of Prominent Research Communities ($\gamma = 1.0$)

| Comm ID | Size (Nodes) | Internal Edges | Leading Researchers | Core Thematic Topics | Dominant Venues |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **#01** | 1,382 | 12,500 | Luke Zettlemoyer, Noah A. Smith, Hannaneh Hajishirzi | NLP, Few-Shot Learning, Multimodal AI, Pre-trained Models | ACL, EMNLP, NeurIPS |
| **#02** | 980 | 11,842 | Zhiyuan Liu, Maosong Sun, Yang Liu | Knowledge Graphs, Information Extraction, NLP, Representation Learning | ACL, AAAI, EMNLP |
| **#03** | 682 | 8,914 | Percy Liang, Christopher D. Manning, Tatsunori Hashimoto | Foundation Models, Language Models, Hallucination, In-Context Learning | NeurIPS, ICML, ICLR |
| **#04** | 566 | 4,210 | Furu Wei, Jianfeng Gao, Weizhu Chen | Transformer Architecture, Cross-Lingual Modeling, Domain Adaptation | ACL, Nature |
| **#05** | 544 | 2,561 | Sergey Levine, Pieter Abbeel, Trevor Darrell | Reinforcement Learning in Robotics, Manipulation, Vision-Language-Action | CVPR, NeurIPS, ICRA |
| **#06** | 511 | 14,021 | Bram van Ginneken, Pheng-Ann Heng, Hao Chen | AI in Cancer Detection, Radiomics, Medical Image Segmentation | IEEE TMI, Nature Comms |
| **#07** | 466 | 5,487 | David Silver, Demis Hassabis, Timothy Lillicrap | Deep RL, Game AI (AlphaGo/Zero), AlphaFold Foundations | Nature, Science |
| **#08** | 415 | 4,870 | Kai-Wei Chang, William Yang Wang, Stella Biderman | NLP Robustness, Open-Source LLMs (EleutherAI), Speech Synthesis | ACL, Findings of EMNLP |
| **#09** | 398 | 2,145 | Philip S. Yu, Shirui Pan, Wenwu Zhu | Graph Neural Networks (GNNs), Data Mining, Node Classification | AAAI, IEEE TKDE |
| **#10** | 390 | 2,610 | Quoc Viet Le, Nicholas Evans, Massimiliano Todisco | Speech Processing, Audio Synthesis, Self-Supervised Learning | NeurIPS, ICASSP |

---

## 5. Temporal Collaboration Dynamics (2016–2025)

### 5.1 Sampling Frame Caveat
As established in the Project-I audit, the dataset was collected via an impact-stratified sampling frame (500 top-cited works per year). Consequently, total publication volume is invariant ($N \approx 500/\text{year}$). Meaningful temporal insights must therefore focus on **structural collaboration indicators**:
1. **Average Team Size:** Number of co-authors per publication $|A(p)|$.
2. **Cross-Institutional Collaboration Rate:** Percentage of publications involving two or more distinct institutions.

### 5.2 Empirical Temporal Trajectory

| Year | Works Analyzed | Mean Team Size (Authors/Paper) | Median Team Size | Cross-Institutional Rate (%) |
| :---: | :---: | :---: | :---: | :---: |
| **2016** | 497 | 4.21 | 3.0 | 53.9% |
| **2017** | 499 | 4.37 | 4.0 | 60.1% |
| **2018** | 500 | 4.86 | 4.0 | 58.6% |
| **2019** | 497 | 5.54 | 4.0 | 59.4% |
| **2020** | 497 | 5.34 | 4.0 | 64.0% |
| **2021** | 499 | 6.32 | 5.0 | 69.1% |
| **2022** | 500 | 6.50 | 5.0 | 63.2% |
| **2023** | 500 | 7.21 | 6.0 | 61.4% |
| **2024** | 500 | 8.19 | 6.0 | 64.0% |
| **2025** | 500 | 9.42 | 7.0 | 72.8% |

### 5.3 Key Structural Observations
1. **The Rise of "Mega-Teams" in AI/ML:** Mean team size more than doubled from **4.21 authors in 2016** to **9.42 authors in 2025**, driven by large foundation model collaborations (e.g., Llama, Bloom, DeepSeek, and AlphaFold teams comprising 50–100+ contributors).
2. **Accelerated Cross-Institutional Integration:** Cross-institutional partnerships grew from **53.9% to 72.8%**, reflecting increasing dependency on multi-organization compute clusters, academic-industry partnerships (e.g. OpenAI/Microsoft, Google DeepMind/Universities), and open-source scientific collectives.

---

## 6. Verification & Generated Visualizations

All analyses and figures were programmatically produced by `src/graph/project_ii_network_analysis.py` and stored in `docs/figures/`:
1. `fig1_degree_distribution.png`: Linear and log-log degree distribution confirming scale-free characteristics.
2. `fig2_community_sizes_and_topics.png`: Size hierarchy and topic distribution of top communities.
3. `fig3_temporal_collaboration_trends.png`: 10-year evolution of team sizes and cross-institutional rates.
4. `fig4_top_centrality_researchers.png`: Comparison of top 10 researchers across PageRank and Newman Strength.
