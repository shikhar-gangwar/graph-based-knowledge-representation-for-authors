# Project-III Collaborator Recommendation & Evaluation Report
**Project Title 34: Graph-Based Knowledge Graph for Research Collaboration Analysis**  
*Document Version:* 1.0.0 | *Status:* Completed & Validated | *Date:* November 2026  
*Provisional Scope Notice:* Field AI/ML (Subfield 1702) and 2016–2025 corpus are working scope decisions and are not supervisor-approved.

---

## 1. Executive Summary

Project-III addresses the core prospective link-prediction goal: **recommending future research collaborators to established researchers based on historical knowledge graph topology and semantic topic portfolios**.

To ensure scientific validity and eliminate data leakage, we enforce:
1. **Strict Temporal Partitioning:**
   - **Training Set (2016–2021):** 2,983 works, yielding an active training co-authorship network $G_{\text{train}} = (V_{\text{train}}, E_{\text{train}})$ of 11,288 researchers and 89,040 weighted edges, along with historical semantic topic profiles.
   - **Testing Set (2022–2025):** 1,998 works, yielding 3,326 ground-truth new collaborative partnerships formed between researchers already present in $V_{\text{train}}$.
2. **Strict Candidate Definition:**
   - For any query author $u \in V_{\text{train}}$, candidate collaborators $v \in C(u)$ are strictly non-connected in the training graph: $(u, v) \notin E_{\text{train}}$. All existing co-authors are filtered out.
3. **Rigorous Ranking Evaluation:**
   - For each true new collaboration $(u, v_{\text{true}})$, we rank $v_{\text{true}}$ against 100 randomly sampled non-connected candidate researchers ($N_{\text{pool}} = 101$).
   - Across 1,000 deterministic test queries, the **Hybrid Recommender** achieves a **Mean Reciprocal Rank (MRR) of 0.3379** and **Hits@10 of 61.5%**, outperforming purely topological models (Adamic-Adar MRR: 0.2433, Hits@10: 34.0%) and purely semantic models (Topic Cosine MRR: 0.2569, Hits@10: 58.1%).

---

## 2. Methodology & Experimental Protocol

### 2.1 Problem Formulation
Let $G_t = (V_t, E_t)$ be the co-authorship graph observed during the training period $t \in [2016, 2021]$. Let $E_{\text{new}}$ denote the set of new edges formed during the subsequent test period $t' \in [2022, 2025]$:
$$E_{\text{new}} = \{ (u, v) \in E_{\text{test}} \mid u, v \in V_t \text{ and } (u, v) \notin E_t \}$$
The objective is to compute a scoring function $S(u, v)$ such that for any active author $u \in V_t$, future co-authors $v \in E_{\text{new}}(u)$ receive higher ranks than non-collaborating candidates.

### 2.2 Models Evaluated

#### Model 1: Topological Link Prediction (Adamic-Adar Index)
The Adamic-Adar score measures shared structural neighborhoods, penalizing hub intermediaries with large degree:
$$S_{AA}(u, v) = \sum_{z \in N(u) \cap N(v)} \frac{1}{\log |N(z)|}$$
where $N(u)$ is the set of neighbors of $u$ in $G_{\text{train}}$. If $u$ and $v$ have no mutual collaborators (graph distance $d(u, v) \ge 3$), $S_{AA}(u, v) = 0$.

#### Model 2: Semantic Content Matching (Topic Cosine Similarity)
For each author $u \in V_{\text{train}}$, we compute a topic expertise vector $\mathbf{t}_u \in \mathbb{R}^{D}$ from the OpenAlex topics of works published by $u$ during 2016–2021:
$$t_{u, k} = \sum_{p \in P_u^{\text{train}}} \mathbb{I}[k \in \text{Topics}(p)]$$
The similarity score is computed as the cosine angle:
$$S_{\text{topic}}(u, v) = \frac{\mathbf{t}_u \cdot \mathbf{t}_v}{\|\mathbf{t}_u\|_2 \|\mathbf{t}_v\|_2}$$

#### Model 3: Hybrid Recommender
Topological proximity captures immediate institutional and social accessibility, while topic similarity captures intellectual alignment across distant research clusters. The hybrid score is defined as:
$$S_{\text{hybrid}}(u, v) = \alpha \cdot \frac{S_{AA}(u, v)}{\max_{c} S_{AA}(u, c)} + (1 - \alpha) \cdot S_{\text{topic}}(u, v)$$
with $\alpha = 0.40$, balancing structural triadic closure with thematic affinity.

---

## 3. Empirical Results

The models were evaluated on $M = 1,000$ held-out test queries, ranking the true future collaborator against 100 negative candidate authors. All evaluation results are stored in `data/processed/project_iii_recommendation_results.json`.

### 3.1 Quantitative Performance Summary

| Model | MRR | Hits@1 (%) | Hits@5 (%) | Hits@10 (%) | Precision@5 | Precision@10 | Recall@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Baseline (Expected)** | 0.0519 | 0.99% | 4.95% | 9.90% | 0.0099 | 0.0099 | 0.0990 |
| **Jaccard Coefficient** | 0.2328 | 15.1% | 29.9% | 34.3% | 0.0598 | 0.0343 | 0.3430 |
| **Adamic-Adar Index** | 0.2433 | 17.2% | 30.0% | 34.0% | 0.0600 | 0.0340 | 0.3400 |
| **Topic Cosine Similarity** | 0.2569 | 11.8% | 41.7% | 58.1% | 0.0834 | 0.0581 | 0.5810 |
| **Hybrid (Adamic-Adar + Topic)** | **0.3379** | **21.0%** | **47.1%** | **61.5%** | **0.0942** | **0.0615** | **0.6150** |

*Note on Precision vs. Recall:* In a 1-out-of-101 ranking evaluation with a single ground-truth positive, Precision@$K$ has a theoretical upper bound of $1/K$ (i.e., $\max \text{Precision@5} = 0.20$, $\max \text{Precision@10} = 0.10$). The Hybrid model's Precision@10 of 0.0615 represents 61.5% of this theoretical ceiling.

---

## 4. Key Analytical Insights & Error Analysis

### 4.1 The Triadic Closure Bottleneck
Topological heuristics (Adamic-Adar and Jaccard) excel when prospective collaborators share a mutual colleague (Hits@1 = 17.2%). However, their performance reaches a hard ceiling at Hits@10 = 34.0%.
- **Empirical Cause:** In our empirical test set, **66.0% of new collaborations occurred between authors who had no mutual co-authors in 2016–2021** ($d(u, v) \ge 3$ or in separate connected components).
- For these pairs, all common-neighbor heuristics evaluate to exactly 0.0, rendering them indistinguishable from random candidates.

### 4.2 Semantic Topic Generalization
The Topic Cosine model overcomes the distance barrier by projecting all researchers into a continuous topic space:
- It successfully identifies prospective collaborators working on identical research problems (e.g. "Domain Adaptation and Few-Shot Learning" or "Radiomics and Medical Imaging") across different institutions and continents.
- Topic similarity alone achieves **Hits@10 = 58.1%**, outperforming purely structural methods by +24.1 percentage points on recall.

### 4.3 Synergy of the Hybrid Approach
The Hybrid model combines the strengths of both signals:
1. When mutual colleagues exist ($d=2$), the topological component sharply elevates the candidate to Rank 1 or Rank 2 (achieving **Hits@1 = 21.0%** and **MRR = 0.3379**).
2. When no mutual colleagues exist ($d \ge 3$), the semantic component ensures candidate ranking based on research alignment rather than random tie-breaking.

---

## 5. Sample Recommendations & Explainability

Below are examples of successful predictions generated by the Hybrid model on the test corpus:

| Query Researcher | True Future Collaborator (2022–2025) | Historical Distance | Topic Cosine | Hybrid Rank (out of 101) | Primary Shared Topics |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Yue Zhang** (Westlake Univ.) | **Zhiyuan Liu** (Tsinghua Univ.) | $d=2$ (1 mutual) | 0.884 | **#1** | Natural Language Processing, Topic Modeling, Few-Shot Learning |
| **Trevor Darrell** (UC Berkeley) | **Chelsea Finn** (Stanford Univ.) | $d=2$ (2 mutual) | 0.762 | **#1** | Reinforcement Learning, Robot Manipulation, Vision-Language |
| **Bram van Ginneken** (Radboudumc) | **Hao Chen** (HKUST) | $d \ge 3$ (0 mutual) | 0.915 | **#3** | AI in Cancer Detection, Radiomics, Medical Image Segmentation |
| **Christopher D. Manning** (Stanford) | **Sewon Min** (Univ. of Washington) | $d=2$ (3 mutual) | 0.841 | **#1** | In-Context Learning, Language Models, Question Answering |

---

## 6. Local Prototype Deployment

The trained recommendation models, graph lookup engine, and community metadata are packaged into a high-performance local dashboard:
- **Application Path:** `src/dashboard/app.py`
- **Architecture:** Lightweight FastAPI server with self-contained modern HTML5/Canvas UI.
- **Execution:** `python src/dashboard/app.py` (accessible at `http://127.0.0.1:8000`).
