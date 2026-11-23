# Data Dictionary: Research Collaboration Knowledge Graph
## OpenAlex AI/ML Corpus (2016–2025)

This document provides field-level definitions, constraints, data types, provenance, and missing-value handling rules for all 8 canonical tables generated in **Project - I**.

---

## 1. Node Tables

### 1.1 `works.csv`
Represents individual scholarly contributions (journal articles, conference papers, book chapters).

| Field Name | Type | Constraints | Missing Rule | Description | Provenance |
|---|---|---|---|---|---|
| `paper_id` | String | Primary Key, Not Null | Reject record if missing | Canonical OpenAlex Work ID (e.g. `W2964177573`) | OpenAlex `id` |
| `doi` | String | Nullable | Empty string if unavailable | Normalized digital object identifier (lowercase, no URL prefix) | OpenAlex `doi` |
| `title` | String | Not Null | Reject record if missing | Cleaned title of the publication | OpenAlex `title` / `display_name` |
| `publication_year` | Integer | Not Null, $[2016, 2025]$ | Reject record if missing | Calendar year of official publication | OpenAlex `publication_year` |
| `citation_count` | Integer | Not Null, $\ge 0$ | Default 0 if absent | Cumulative global citation count | OpenAlex `cited_by_count` |
| `type` | String | Not Null | Default `article` | Publication format (`article`, `conference-paper`, `book-chapter`) | OpenAlex `type` |
| `venue_id` | String | Foreign Key, Nullable | Empty string if no venue | Foreign key to `venues.csv` | OpenAlex `primary_location.source.id` |
| `abstract` | String | Nullable | Empty string if unavailable | Continuous text reconstructed from inverted index. Never fabricated. | OpenAlex `abstract_inverted_index` |

---

### 1.2 `authors.csv`
Represents individual researchers.

| Field Name | Type | Constraints | Missing Rule | Description | Provenance |
|---|---|---|---|---|---|
| `author_id` | String | Primary Key, Not Null | Generate deterministic fallback | Canonical OpenAlex Author ID (e.g. `A5057457287`). If missing, fallback `A_anon_{hash}` | OpenAlex `author.id` |
| `name` | String | Not Null | Reject authorship if empty | Full researcher display name | OpenAlex `author.display_name` |
| `orcid` | String | Nullable | Empty string if missing | Verified ORCID URI (e.g. `https://orcid.org/0000-...`) | OpenAlex `author.orcid` |

*Note: Author email addresses are strictly excluded.*

---

### 1.3 `institutions.csv`
Represents universities, industrial research laboratories, and research institutions.

| Field Name | Type | Constraints | Missing Rule | Description | Provenance |
|---|---|---|---|---|---|
| `institution_id` | String | Primary Key, Not Null | Reject record if missing | Canonical OpenAlex Institution ID (e.g. `I123456789`) | OpenAlex `institutions.id` |
| `name` | String | Not Null | Reject if missing | Official institutional display name | OpenAlex `display_name` |
| `country_code` | String | Nullable, 2 chars | Empty string if unknown | ISO 3166-1 alpha-2 country code (e.g. `US`, `GB`, `CN`, `IN`) | OpenAlex `country_code` |
| `ror` | String | Nullable | Empty string if unknown | Research Organization Registry canonical URI | OpenAlex `ror` |
| `type` | String | Nullable | Empty string if unknown | Institution category (`education`, `company`, `facility`, `nonprofit`) | OpenAlex `type` |

---

### 1.4 `venues.csv`
Represents dissemination venues (conferences, journals, repositories).

| Field Name | Type | Constraints | Missing Rule | Description | Provenance |
|---|---|---|---|---|---|
| `venue_id` | String | Primary Key, Not Null | Reject if missing | Canonical OpenAlex Source ID (e.g. `S123456789`) | OpenAlex `source.id` |
| `name` | String | Not Null | Reject if missing | Name of the journal or conference proceedings | OpenAlex `source.display_name` |
| `type` | String | Nullable | Default `journal` | Venue channel type (`journal`, `conference`, `repository`) | OpenAlex `source.type` |
| `issn` | String | Nullable | Empty string if missing | International Standard Serial Number (ISSN-L) | OpenAlex `source.issn_l` |
| `publisher` | String | Nullable | Empty string if missing | Host publishing organization name | OpenAlex `host_organization_name` |

---

### 1.5 `topics.csv`
Represents scientific research topics, concepts, and domains from OpenAlex Topics 2024 Taxonomy.

| Field Name | Type | Constraints | Missing Rule | Description | Provenance |
|---|---|---|---|---|---|
| `topic_id` | String | Primary Key, Not Null | Reject if missing | Canonical OpenAlex Topic ID (e.g. `T10181`) | OpenAlex `topics.id` |
| `name` | String | Not Null | Reject if missing | Human-readable scientific topic title | OpenAlex `topics.display_name` |
| `subfield` | String | Not Null | Default `Artificial Intelligence` | Specialized subdiscipline name | OpenAlex `subfield.display_name` |
| `field` | String | Not Null | Default `Computer Science` | Disciplinary field name | OpenAlex `field.display_name` |
| `domain` | String | Not Null | Default `Physical Sciences` | Overarching scientific domain | OpenAlex `domain.display_name` |

---

## 2. Relationship (Edge) Tables

### 2.1 `authorships.csv`
Associates an author with a publication.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `author_id` | String | Foreign Key referencing `authors.csv` | Researcher identifier |
| `paper_id` | String | Foreign Key referencing `works.csv` | Publication identifier |
| `author_position` | Integer | Not Null, $\ge 1$ | 1-based order of authorship (1 = lead author) |
| `is_corresponding` | Boolean | Not Null (`true`/`false`) | Indicates whether author was corresponding contact |

---

### 2.2 `affiliations.csv`
Associates an author's contribution on a specific paper with an institution.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `author_id` | String | Foreign Key referencing `authors.csv` | Researcher identifier |
| `institution_id` | String | Foreign Key referencing `institutions.csv` | Canonical institution identifier |
| `paper_id` | String | Foreign Key referencing `works.csv` | Publication context/provenance link |

---

### 2.3 `work_topics.csv`
Associates a publication with a research topic concept.

| Field Name | Type | Constraints | Description |
|---|---|---|---|
| `paper_id` | String | Foreign Key referencing `works.csv` | Publication identifier |
| `topic_id` | String | Foreign Key referencing `topics.csv` | Canonical topic identifier |
| `score` | Float | Not Null, $[0.0, 1.0]$ | OpenAlex classifier confidence score |
