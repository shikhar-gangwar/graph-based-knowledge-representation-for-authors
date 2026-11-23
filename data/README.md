# Dataset Documentation & Provenance: OpenAlex AI/ML Corpus (2016–2025)

---

## 1. Source Identification & Version

- **Primary Source:** OpenAlex Works API ([Official OpenAlex Documentation](https://help.openalex.org/api/))
- **Base Endpoint:** `https://api.openalex.org/works`
- **Topic Taxonomy:** OpenAlex Topics 2024 Taxonomy
- **Primary Domain & Subfield Filter:** Subfield `1702` (*Artificial Intelligence*) under Field *Computer Science* (Field `17`) and Domain *Physical Sciences* (Domain `10`).
- **Retrieval Date:** 2026-11-22
- **License / Data Terms:** Creative Commons CC0 1.0 Universal (Public Domain Dedication).
- **Recommended Attribution:** OpenAlex (OurResearch), `https://openalex.org/`.

---

## 2. Scope & Inclusion Specification

- **Target Research Discipline:** Artificial Intelligence & Machine Learning.
- **Publication Temporal Scope:** 2016 through 2025 inclusive (10 calendar years).
- **Publication Types:** Peer-reviewed journal articles (`article`), conference proceedings (`conference-paper`), and authoritative scholarly book chapters (`book-chapter`).
- **Quality Filters:** 
  - `is_retracted:false` (excludes withdrawn publications).
  - `is_paratext:false` (excludes covers, prefaces, and table of contents entries).
- **Sampling Methodology:** Deterministic year-stratified sampling.
  - Quota: Exactly 500 works requested per calendar year ($10 \text{ years} \times 500 = 5,000 \text{ raw works}$).
  - Ranking function: `sort=cited_by_count:desc` within each year stratum to select high-impact anchor papers with rich author and institutional citation graphs.
- **Status of Scope:** **Provisional working scope**, not yet supervisor-approved.

---

## 3. Privacy & Personal Information Policy

- **Author Email Policy:** In accordance with project instructions and academic data privacy standards, **author email addresses are completely excluded** from all raw snapshots, processing pipelines, derived CSV tables, and graph representations.
- **Attribution Metadata:** Only public scholarly attribution metadata (author names, persistent OpenAlex Author IDs, public ORCIDs, and institutional affiliations) are processed.

---

## 4. Dataset Files & Row Counts

### 4.1 Raw Source Data (`data/raw/`)
- `data/raw/openalex_raw_5000.json` (Size $\approx$ 26.5 MB): 5,000 raw JSON objects directly retrieved from OpenAlex API.
- `data/raw/openalex_collection_log.json`: Collection audit metadata logging queries, filters, quotas, and retrieval dates.

### 4.2 Canonical Processed Relational Tables (`data/processed/` and `data/graph_ready/`)

| Filename | Row Count | Primary Key | Description |
|---|---|---|---|
| `works.csv` | **4,989** | `paper_id` | Deduplicated AI/ML publications (11 duplicates removed from raw 5,000). |
| `authors.csv` | **22,185** | `author_id` | Unique researchers with canonical OpenAlex IDs and verified ORCIDs. |
| `institutions.csv` | **2,738** | `institution_id` | Unique academic universities, labs, and companies with ROR identifiers. |
| `venues.csv` | **904** | `venue_id` | Publishing channels (journals, conferences) with ISSNs. |
| `topics.csv` | **519** | `topic_id` | Standardized research topics within the OpenAlex topic hierarchy. |
| `authorships.csv` | **30,930** | `(paper_id, author_id)` | Work-to-author contribution edges with authorship position. |
| `affiliations.csv` | **33,410** | `(author_id, institution_id, paper_id)` | Author institutional affiliation edges anchored to specific papers. |
| `work_topics.csv` | **14,967** | `(paper_id, topic_id)` | Work-to-topic semantic classification edges with confidence scores. |

---

## 5. Year Distribution (2016–2025)

| Year | Unique Works | Percentage | Cumulative Works |
|---|---|---|---|
| **2016** | 497 | 10.0% | 497 |
| **2017** | 499 | 10.0% | 996 |
| **2018** | 500 | 10.0% | 1,496 |
| **2019** | 497 | 10.0% | 1,993 |
| **2020** | 497 | 10.0% | 2,490 |
| **2021** | 499 | 10.0% | 2,989 |
| **2022** | 500 | 10.0% | 3,489 |
| **2023** | 500 | 10.0% | 3,989 |
| **2024** | 500 | 10.0% | 4,489 |
| **2025** | 500 | 10.0% | 4,989 |
| **Total** | **4,989** | **100.0%** | **4,989** |
