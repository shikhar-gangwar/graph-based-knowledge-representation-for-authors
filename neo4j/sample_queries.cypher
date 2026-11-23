// ==============================================================================
// NEO4J SAMPLE ANALYTICAL QUERIES
// Project Title: Graph-Based Knowledge Graph for Research Collaboration Analysis
// These Cypher queries demonstrate collaboration analysis, community subgraphs,
// institutional bridges, and researcher ranking.
// ==============================================================================

// ------------------------------------------------------------------------------
// QUERY 1: Top 10 Most Prolific Authors with Citation Counts
// ------------------------------------------------------------------------------
MATCH (a:Author)-[:AUTHORED]->(p:Publication)
RETURN 
    a.name AS Author_Name,
    a.orcid AS ORCID,
    count(p) AS Paper_Count,
    sum(p.citation_count) AS Total_Citations
ORDER BY Paper_Count DESC, Total_Citations DESC
LIMIT 10;

// ------------------------------------------------------------------------------
// QUERY 2: Strongest Co-authorship Collaborations (Newman Weighted Edges)
// ------------------------------------------------------------------------------
MATCH (a1:Author)-[r:CO_AUTHORED_WITH]-(a2:Author)
WHERE id(a1) < id(a2)
RETURN 
    a1.name AS Researcher_1,
    a2.name AS Researcher_2,
    r.papers_count AS Joint_Papers,
    r.weight AS Collaboration_Strength
ORDER BY r.weight DESC
LIMIT 10;

// ------------------------------------------------------------------------------
// QUERY 3: Cross-Institutional Collaborations
// Identifies papers produced across different universities or research labs
// ------------------------------------------------------------------------------
MATCH (a1:Author)-[:AFFILIATED_WITH]->(i1:Institution)
MATCH (a1)-[:AUTHORED]->(p:Publication)<-[:AUTHORED]-(a2:Author)
MATCH (a2)-[:AFFILIATED_WITH]->(i2:Institution)
WHERE i1 <> i2 AND id(i1) < id(i2)
RETURN 
    i1.name AS Institution_A,
    i2.name AS Institution_B,
    count(DISTINCT p) AS Joint_Publications
ORDER BY Joint_Publications DESC
LIMIT 10;

// ------------------------------------------------------------------------------
// QUERY 4: Ego-Network of a Specified Author (1-hop Collaborators & Topics)
// ------------------------------------------------------------------------------
MATCH (target:Author {name: "Jure Leskovec"})
OPTIONAL MATCH (target)-[r:CO_AUTHORED_WITH]-(collab:Author)
OPTIONAL MATCH (target)-[:AUTHORED]->(p:Publication)-[:HAS_TOPIC]->(t:Topic)
RETURN 
    target.name AS Target,
    collect(DISTINCT collab.name)[..10] AS Top_Collaborators,
    collect(DISTINCT t.name)[..10] AS Associated_Topics;

// ------------------------------------------------------------------------------
// QUERY 5: Shortest Path Between Two Researchers
// Reveals intermediary bridges connecting two separate research communities
// ------------------------------------------------------------------------------
MATCH (a1:Author), (a2:Author)
WHERE a1.name = "Yoshua Bengio" AND a2.name = "Jure Leskovec"
MATCH path = shortestPath((a1)-[:CO_AUTHORED_WITH*..6]-(a2))
RETURN path;

// ------------------------------------------------------------------------------
// QUERY 6: Top Research Topics by Publication Volume and Average Citations
// ------------------------------------------------------------------------------
MATCH (t:Topic)<-[:HAS_TOPIC]-(p:Publication)
RETURN 
    t.name AS Topic_Name,
    t.field AS Field,
    count(p) AS Publication_Count,
    avg(p.citation_count) AS Avg_Citations
ORDER BY Publication_Count DESC
LIMIT 15;

// ------------------------------------------------------------------------------
// QUERY 7: Interdisciplinary Paper Discovery
// Finds papers that connect multiple distinct high-level domains
// ------------------------------------------------------------------------------
MATCH (p:Publication)-[:HAS_TOPIC]->(t:Topic)
WITH p, collect(DISTINCT t.field) AS fields, collect(DISTINCT t.name) AS topics
WHERE size(fields) > 1
RETURN 
    p.title AS Paper_Title,
    p.publication_year AS Year,
    fields AS Bridged_Fields,
    topics[..5] AS Key_Topics
LIMIT 10;

// ------------------------------------------------------------------------------
// QUERY 8: Highly Cited Publication Cascades (Internal Citation Subgraph)
// ------------------------------------------------------------------------------
MATCH (p1:Publication)-[:CITES]->(p2:Publication)
RETURN 
    p2.title AS Cited_Work,
    count(p1) AS Internal_Citations
ORDER BY Internal_Citations DESC
LIMIT 10;
