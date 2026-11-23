// ==============================================================================
// NEO4J DATA INGESTION SCRIPT (LOAD CSV)
// Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis
// Instructions:
// 1. Copy CSV files from `data/graph_ready/` into the Neo4j `import` directory
//    (or configure `dbms.security.allow_csv_import_from_file_urls=true`).
// 2. Execute each block sequentially in Neo4j Browser or cypher-shell.
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. IMPORT NODE ENTITIES
// ------------------------------------------------------------------------------

// 1.1 Import Publications
LOAD CSV WITH HEADERS FROM 'file:///nodes_publication.csv' AS row
MERGE (p:Publication {paper_id: row.`paper_id:ID(Publication)`})
ON CREATE SET 
    p.doi = row.doi,
    p.title = row.title,
    p.publication_year = toInteger(row.`publication_year:int`),
    p.citation_count = toInteger(row.`citation_count:int`),
    p.type = row.type,
    p.abstract = row.abstract;

// 1.2 Import Authors (Disambiguated Canonical Entities)
LOAD CSV WITH HEADERS FROM 'file:///nodes_author.csv' AS row
MERGE (a:Author {author_id: row.`author_id:ID(Author)`})
ON CREATE SET 
    a.name = row.name,
    a.orcid = row.orcid,
    a.merged_count = toInteger(row.`merged_count:int`);

// 1.3 Import Institutions
LOAD CSV WITH HEADERS FROM 'file:///nodes_institution.csv' AS row
MERGE (i:Institution {institution_id: row.`institution_id:ID(Institution)`})
ON CREATE SET 
    i.name = row.name,
    i.country_code = row.country_code,
    i.ror = row.ror;

// 1.4 Import Venues
LOAD CSV WITH HEADERS FROM 'file:///nodes_venue.csv' AS row
MERGE (v:Venue {venue_id: row.`venue_id:ID(Venue)`})
ON CREATE SET 
    v.name = row.name,
    v.type = row.type,
    v.issn = row.issn;

// 1.5 Import Topics & Extracted Keywords
LOAD CSV WITH HEADERS FROM 'file:///nodes_topic.csv' AS row
MERGE (t:Topic {topic_id: row.`topic_id:ID(Topic)`})
ON CREATE SET 
    t.name = row.name,
    t.subfield = row.subfield,
    t.field = row.field,
    t.domain = row.domain;

// ------------------------------------------------------------------------------
// 2. IMPORT RELATIONSHIP EDGES
// ------------------------------------------------------------------------------

// 2.1 Import AUTHORED Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_authored.csv' AS row
MATCH (a:Author {author_id: row.`:START_ID(Author)`})
MATCH (p:Publication {paper_id: row.`:END_ID(Publication)`})
MERGE (a)-[r:AUTHORED]->(p)
ON CREATE SET 
    r.author_position = toInteger(row.`author_position:int`),
    r.is_corresponding = toBoolean(row.`is_corresponding:boolean`);

// 2.2 Import AFFILIATED_WITH Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_affiliated_with.csv' AS row
MATCH (a:Author {author_id: row.`:START_ID(Author)`})
MATCH (i:Institution {institution_id: row.`:END_ID(Institution)`})
MERGE (a)-[:AFFILIATED_WITH]->(i);

// 2.3 Import PUBLISHED_IN Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_published_in.csv' AS row
MATCH (p:Publication {paper_id: row.`:START_ID(Publication)`})
MATCH (v:Venue {venue_id: row.`:END_ID(Venue)`})
MERGE (p)-[:PUBLISHED_IN]->(v);

// 2.4 Import HAS_TOPIC Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_has_topic.csv' AS row
MATCH (p:Publication {paper_id: row.`:START_ID(Publication)`})
MATCH (t:Topic {topic_id: row.`:END_ID(Topic)`})
MERGE (p)-[r:HAS_TOPIC]->(t)
ON CREATE SET r.score = toFloat(row.`score:float`);

// 2.5 Import Internal CITES Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_cites.csv' AS row
MATCH (p1:Publication {paper_id: row.`:START_ID(Publication)`})
MATCH (p2:Publication {paper_id: row.`:END_ID(Publication)`})
MERGE (p1)-[:CITES]->(p2);

// 2.6 Import Pre-computed Weighted CO_AUTHORED_WITH Edges
LOAD CSV WITH HEADERS FROM 'file:///edges_co_authored_with.csv' AS row
MATCH (a1:Author {author_id: row.`:START_ID(Author)`})
MATCH (a2:Author {author_id: row.`:END_ID(Author)`})
MERGE (a1)-[r:CO_AUTHORED_WITH]-(a2)
ON CREATE SET 
    r.weight = toFloat(row.`weight:float`),
    r.papers_count = toInteger(row.`papers_count:int`);
