// ==============================================================================
// NEO4J IDEMPOTENT SCHEMA & DATA LOAD SPECIFICATION FOR D3 CORPUS
// Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis
// Dataset: DBLP Discovery Dataset (D3) AI/ML Subset (2016-2025)
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. IDEMPOTENT CONSTRAINTS & INDEXES
// ------------------------------------------------------------------------------

CREATE CONSTRAINT unique_d3_paper IF NOT EXISTS
FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE;

CREATE CONSTRAINT unique_d3_author IF NOT EXISTS
FOR (a:Author) REQUIRE a.author_id IS UNIQUE;

CREATE CONSTRAINT unique_d3_venue IF NOT EXISTS
FOR (v:Venue) REQUIRE v.venue_id IS UNIQUE;

CREATE CONSTRAINT unique_d3_topic IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;

CREATE INDEX index_d3_author_name IF NOT EXISTS
FOR (a:Author) ON (a.name);

CREATE INDEX index_d3_paper_year IF NOT EXISTS
FOR (p:Paper) ON (p.year);

CREATE INDEX index_d3_paper_citations IF NOT EXISTS
FOR (p:Paper) ON (p.citation_count);

CREATE FULLTEXT INDEX fulltext_d3_paper IF NOT EXISTS
FOR (p:Paper) ON EACH [p.title, p.abstract];

// ------------------------------------------------------------------------------
// 2. IDEMPOTENT NODE INGESTION (LOAD CSV)
// Copy data/graph_ready/*.csv to Neo4j import directory before running.
// ------------------------------------------------------------------------------

// 2.1 Ingest Paper Nodes
LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
MERGE (p:Paper {paper_id: row.paper_id})
ON CREATE SET 
    p.doi = row.doi,
    p.dblp_key = row.dblp_key,
    p.title = row.title,
    p.year = toInteger(row.year),
    p.citation_count = toInteger(row.citation_count),
    p.reference_count = toInteger(row.reference_count),
    p.abstract = row.abstract;

// 2.2 Ingest Author Nodes (Emails excluded by design)
LOAD CSV WITH HEADERS FROM 'file:///authors.csv' AS row
MERGE (a:Author {author_id: row.author_id})
ON CREATE SET 
    a.name = row.name;

// 2.3 Ingest Venue Nodes
LOAD CSV WITH HEADERS FROM 'file:///venues.csv' AS row
MERGE (v:Venue {venue_id: row.venue_id})
ON CREATE SET 
    v.name = row.name;

// 2.4 Ingest CSO Topic Nodes
LOAD CSV WITH HEADERS FROM 'file:///topics.csv' AS row
MERGE (t:Topic {topic_id: row.topic_id})
ON CREATE SET 
    t.name = row.name;

// ------------------------------------------------------------------------------
// 3. IDEMPOTENT RELATIONSHIP INGESTION
// ------------------------------------------------------------------------------

// 3.1 AUTHORED Relationships
LOAD CSV WITH HEADERS FROM 'file:///authorships.csv' AS row
MATCH (a:Author {author_id: row.author_id})
MATCH (p:Paper {paper_id: row.paper_id})
MERGE (a)-[r:AUTHORED]->(p)
ON CREATE SET r.author_position = toInteger(row.author_position);

// 3.2 PUBLISHED_IN Relationships
LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
WHERE row.venue_id IS NOT NULL AND row.venue_id <> 'V_unknown'
MATCH (p:Paper {paper_id: row.paper_id})
MATCH (v:Venue {venue_id: row.venue_id})
MERGE (p)-[:PUBLISHED_IN]->(v);

// 3.3 HAS_TOPIC Relationships
LOAD CSV WITH HEADERS FROM 'file:///work_topics.csv' AS row
MATCH (p:Paper {paper_id: row.paper_id})
MATCH (t:Topic {topic_id: row.topic_id})
MERGE (p)-[:HAS_TOPIC]->(t);

// 3.4 Weighted CO_AUTHORED_WITH Relationships (Newman Projection)
LOAD CSV WITH HEADERS FROM 'file:///coauthorship_edges.csv' AS row
MATCH (a1:Author {author_id: row.author_id_1})
MATCH (a2:Author {author_id: row.author_id_2})
MERGE (a1)-[r:CO_AUTHORED_WITH]-(a2)
ON CREATE SET 
    r.weight = toFloat(row.weight),
    r.papers_count = toInteger(row.papers_count);
