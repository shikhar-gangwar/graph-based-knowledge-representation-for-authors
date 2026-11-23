// ==============================================================================
// NEO4J IDEMPOTENT SCHEMA & CONSTRAINTS SPECIFICATION
// Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis
// Target Database: Neo4j 5.x
// Entities: Paper, Author, Institution, Venue, Topic
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. PRIMARY KEY UNIQUENESS CONSTRAINTS
// ------------------------------------------------------------------------------

CREATE CONSTRAINT unique_paper_id IF NOT EXISTS
FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE;

CREATE CONSTRAINT unique_author_id IF NOT EXISTS
FOR (a:Author) REQUIRE a.author_id IS UNIQUE;

CREATE CONSTRAINT unique_institution_id IF NOT EXISTS
FOR (i:Institution) REQUIRE i.institution_id IS UNIQUE;

CREATE CONSTRAINT unique_venue_id IF NOT EXISTS
FOR (v:Venue) REQUIRE v.venue_id IS UNIQUE;

CREATE CONSTRAINT unique_topic_id IF NOT EXISTS
FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;

// ------------------------------------------------------------------------------
// 2. QUERY OPTIMIZATION INDEXES
// ------------------------------------------------------------------------------

// Author name and ORCID index
CREATE INDEX index_author_name IF NOT EXISTS
FOR (a:Author) ON (a.name);

CREATE INDEX index_author_orcid IF NOT EXISTS
FOR (a:Author) ON (a.orcid);

// Paper publication year and citation count indexes
CREATE INDEX index_paper_year IF NOT EXISTS
FOR (p:Paper) ON (p.publication_year);

CREATE INDEX index_paper_citations IF NOT EXISTS
FOR (p:Paper) ON (p.citation_count);

CREATE INDEX index_paper_doi IF NOT EXISTS
FOR (p:Paper) ON (p.doi);

// Institution country and ROR index
CREATE INDEX index_inst_country IF NOT EXISTS
FOR (i:Institution) ON (i.country_code);

CREATE INDEX index_inst_ror IF NOT EXISTS
FOR (i:Institution) ON (i.ror);

// Topic name and subfield index
CREATE INDEX index_topic_name IF NOT EXISTS
FOR (t:Topic) ON (t.name);

CREATE INDEX index_topic_subfield IF NOT EXISTS
FOR (t:Topic) ON (t.subfield);

// Fulltext search index on paper titles and abstracts
CREATE FULLTEXT INDEX fulltext_paper_text IF NOT EXISTS
FOR (p:Paper) ON EACH [p.title, p.abstract];

// Fulltext search index on author and institution names
CREATE FULLTEXT INDEX fulltext_entity_names IF NOT EXISTS
FOR (a:Author, i:Institution) ON EACH [a.name, i.name];
