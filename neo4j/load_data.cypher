// ==============================================================================
// NEO4J DATA INGESTION SCRIPT (LOAD CSV)
// Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis
// Ingestion Target: 8 Canonical Project-I Tables
// Instructions:
// 1. Copy all CSV files from `data/processed/` (or `data/graph_ready/`) to your
//    Neo4j `import/` directory.
// 2. Ensure `schema.cypher` has been executed first to establish constraints.
// 3. Run each ingestion statement below sequentially.
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. INGEST NODE ENTITIES (Idempotent MERGE)
// ------------------------------------------------------------------------------

// 1.1 Ingest Papers
LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
MERGE (p:Paper {paper_id: row.paper_id})
ON CREATE SET 
    p.doi = row.doi,
    p.title = row.title,
    p.publication_year = toInteger(row.publication_year),
    p.citation_count = toInteger(row.citation_count),
    p.type = row.type,
    p.abstract = row.abstract;

// 1.2 Ingest Authors (Emails Excluded)
LOAD CSV WITH HEADERS FROM 'file:///authors.csv' AS row
MERGE (a:Author {author_id: row.author_id})
ON CREATE SET 
    a.name = row.name,
    a.orcid = row.orcid;

// 1.3 Ingest Institutions
LOAD CSV WITH HEADERS FROM 'file:///institutions.csv' AS row
MERGE (i:Institution {institution_id: row.institution_id})
ON CREATE SET 
    i.name = row.name,
    i.country_code = row.country_code,
    i.ror = row.ror,
    i.type = row.type;

// 1.4 Ingest Venues
LOAD CSV WITH HEADERS FROM 'file:///venues.csv' AS row
MERGE (v:Venue {venue_id: row.venue_id})
ON CREATE SET 
    v.name = row.name,
    v.type = row.type,
    v.issn = row.issn,
    v.publisher = row.publisher;

// 1.5 Ingest Topics
LOAD CSV WITH HEADERS FROM 'file:///topics.csv' AS row
MERGE (t:Topic {topic_id: row.topic_id})
ON CREATE SET 
    t.name = row.name,
    t.subfield = row.subfield,
    t.field = row.field,
    t.domain = row.domain;

// ------------------------------------------------------------------------------
// 2. INGEST RELATIONSHIP EDGES
// ------------------------------------------------------------------------------

// 2.1 Ingest AUTHORED Relationships
LOAD CSV WITH HEADERS FROM 'file:///authorships.csv' AS row
MATCH (a:Author {author_id: row.author_id})
MATCH (p:Paper {paper_id: row.paper_id})
MERGE (a)-[r:AUTHORED]->(p)
ON CREATE SET 
    r.author_position = toInteger(row.author_position),
    r.is_corresponding = toBoolean(row.is_corresponding);

// 2.2 Ingest AFFILIATED_WITH Relationships
LOAD CSV WITH HEADERS FROM 'file:///affiliations.csv' AS row
MATCH (a:Author {author_id: row.author_id})
MATCH (i:Institution {institution_id: row.institution_id})
MERGE (a)-[r:AFFILIATED_WITH {paper_id: row.paper_id}]->(i);

// 2.3 Ingest PUBLISHED_IN Relationships
LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
WHERE row.venue_id IS NOT NULL AND row.venue_id <> ''
MATCH (p:Paper {paper_id: row.paper_id})
MATCH (v:Venue {venue_id: row.venue_id})
MERGE (p)-[:PUBLISHED_IN]->(v);

// 2.4 Ingest HAS_TOPIC Relationships
LOAD CSV WITH HEADERS FROM 'file:///work_topics.csv' AS row
MATCH (p:Paper {paper_id: row.paper_id})
MATCH (t:Topic {topic_id: row.topic_id})
MERGE (p)-[r:HAS_TOPIC]->(t)
ON CREATE SET r.score = toFloat(row.score);
