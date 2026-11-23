"""
Execute segmented git initialization and commit history generation.
Completes remaining commits (18 through 61) with atomic, chronological Conventional Commits.
"""

import os
import subprocess
import sys

remaining_commits = [
    # Phase 5: Author Name Disambiguation & Entity Resolution
    ('feat(nlp): implement author disambiguation and institutional resolution engine',
     ['src/nlp/disambiguate_and_extract.py']),
    ('data(nlp): export canonical author entities from disambiguation pipeline',
     ['data/processed/canonical_authors.json']),
    ('data(nlp): export author entity records with normalized names and aliases',
     ['data/processed/authors.json']),
    ('data(nlp): export disambiguated author-work contribution links',
     ['data/processed/disambiguated_authored_links.json']),
    ('data(nlp): export disambiguated institutional affiliation links',
     ['data/processed/disambiguated_affiliated_links.json']),
    ('data(nlp): record author name disambiguation (AND) evaluation benchmarks',
     ['data/processed/and_evaluation_stats.json']),

    # Phase 6: Canonical Relational Entities & Relational Tables (Project-I)
    ('data(processed): generate canonical publications relational table with citation counts',
     ['data/processed/works.csv']),
    ('data(processed): generate structured publications JSON database',
     ['data/processed/publications.json']),
    ('data(processed): generate unique author entities with ORCID identifiers',
     ['data/processed/authors.csv']),
    ('data(processed): generate academic institutions and publication venues tables',
     ['data/processed/institutions.csv', 'data/processed/venues.csv']),
    ('data(processed): generate institutions and venues JSON entity collections',
     ['data/processed/institutions.json', 'data/processed/venues.json']),
    ('data(processed): generate OpenAlex taxonomy topics and work-topic mappings',
     ['data/processed/topics.csv', 'data/processed/work_topics.csv']),
    ('data(processed): generate topics JSON datasets and semantic concept hierarchies',
     ['data/processed/topics.json', 'data/processed/enriched_topics.json']),
    ('data(processed): generate publication-to-topic relationship edge links',
     ['data/processed/has_topic_links.json', 'data/processed/enriched_has_topic_links.json']),
    ('data(processed): generate work authorship contribution edges',
     ['data/processed/authorships.csv', 'data/processed/authored_links.json']),
    ('data(processed): generate institutional affiliation and venue publication links',
     ['data/processed/affiliations.csv', 'data/processed/affiliated_links.json', 'data/processed/published_in_links.json']),
    ('data(processed): generate inter-paper citation graph links',
     ['data/processed/citation_links.json']),

    # Phase 7: Neo4j Ingestion, Schema & Queries
    ('feat(neo4j): configure Docker container infrastructure for Neo4j 5.x graph database',
     ['docker-compose.yml']),
    ('feat(neo4j): define Cypher constraints, node labels, and relationship indexes',
     ['neo4j/schema.cypher', 'neo4j/d3_schema_and_load.cypher']),
    ('feat(neo4j): implement idempotent LOAD CSV ingestion pipelines',
     ['neo4j/load_data.cypher', 'neo4j/import_data.cypher']),
    ('feat(neo4j): provide analytical Cypher queries for co-authorship and centrality inspection',
     ['neo4j/sample_queries.cypher']),
    ('docs(schema): document heterogeneous graph schema and metadata dictionary',
     ['docs/graph_schema.md', 'docs/data_dictionary.md']),

    # Phase 8: Quality Assurance & Project-I Sign-off
    ('test(audit): implement pilot quality auditor and metrics assessment suite',
     ['src/audit/audit_pilot_and_metrics.py']),
    ('test(audit): implement comprehensive referential integrity and quality auditor',
     ['src/audit/audit_project_i_quality.py']),
    ('test(audit): add master Project-I validation execution harness',
     ['src/validate_project_1.py', 'run_project_1.py']),
    ('docs(audit): publish Project-I methodology, pilot audit, and completion reports',
     ['docs/project_i_methodology.md', 'docs/pilot_audit_report.md', 'docs/project_i_completion_report.md', 'docs/project_1_report.md']),

    # Phase 9: Graph Projection & Project-II Network Analysis
    ('feat(graph): implement weighted co-authorship graph builder with Newman collaboration weights',
     ['src/graph/build_coauthorship_graph.py']),
    ('data(graph): export co-authorship network node and edge relational lists',
     ['data/processed/coauthorship_nodes.csv', 'data/processed/coauthorship_edges.csv']),
    ('feat(graph): implement multi-resolution Louvain community detection engine',
     ['src/graph/analyze_communities.py', 'data/processed/community_analysis_results.json']),
    ('feat(graph): implement end-to-end Project-II network topology and centrality analyzer',
     ['src/graph/project_ii_network_analysis.py', 'data/processed/project_ii_results.json']),
    ('feat(graph): export Neo4j-ready heterogeneous graph tables',
     ['src/graph/export_graph_tables.py', 'data/graph_ready']),

    # Phase 10: Publication-Quality Empirical Visualizations
    ('docs(viz): generate Figure 1 - degree distribution and power-law scaling analysis',
     ['docs/figures/fig1_degree_distribution.png']),
    ('docs(viz): generate Figure 2 - Louvain community size distribution and topical composition',
     ['docs/figures/fig2_community_sizes_and_topics.png']),
    ('docs(viz): generate Figure 3 - 10-year longitudinal collaboration trends and team expansion',
     ['docs/figures/fig3_temporal_collaboration_trends.png']),
    ('docs(viz): generate Figure 4 - PageRank vs. collaboration strength for top researchers',
     ['docs/figures/fig4_top_centrality_researchers.png']),

    # Phase 11: Project-III Collaborator Recommendation Engine
    ('feat(recommendation): implement strict temporal train/test split link predictor',
     ['src/recommendation/collaborator_recommender.py']),
    ('data(recommendation): export link prediction evaluation benchmarks and MRR metrics',
     ['data/processed/project_iii_recommendation_results.json']),
    ('docs(analysis): publish Project-II network analysis and topological characterization report',
     ['docs/project_ii_analysis_report.md']),
    ('docs(recommendation): publish Project-III prospective collaborator recommendation report',
     ['docs/project_iii_recommendation_report.md']),

    # Phase 12: ScholarlyKG Interactive Dashboard & Web Prototype
    ('feat(dashboard): develop FastAPI analytics backend with ego-network and recommendation APIs',
     ['src/dashboard/app.py']),
    ('feat(dashboard): build responsive SVG force-directed network visualizer and analytics UI',
     ['src/dashboard/index.html']),
    ('test(dashboard): add automated test suite verifying all REST API endpoints',
     ['src/dashboard/test_dashboard.py']),
    ('feat(dashboard): add root launch entrypoints, multi-port fallback, and Windows runner',
     ['app.py', 'run_dashboard.py', 'run_dashboard.bat', 'scripts/apply_fixes.py', 'scripts/verify_render.py']),
    ('docs(thesis): publish comprehensive final project report, thesis outline, and master README',
     ['docs/final_project_report.md', 'docs/final_report_and_presentation_outline.md', 'README.md'])
]

def run(cmd):
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print(f"FAILED: {cmd}")
        print("STDERR:", p.stderr)
        sys.exit(p.returncode)
    return p.stdout.strip()

def main():
    existing_count = int(run("git rev-list --count HEAD"))
    print(f"Starting from existing {existing_count} commits...")

    for idx, (msg, targets) in enumerate(remaining_commits, existing_count + 1):
        for t in targets:
            run(f"git add \"{t}\"")
        
        status = run("git status --porcelain")
        if status:
            run(f"git commit -m \"{msg}\"")
            h = run("git rev-parse --short HEAD")
            print(f"[{idx:02d}] {h}: {msg.splitlines()[0]}")
        else:
            print(f"[{idx:02d}] SKIPPED (No staged changes): {msg}")

    # Check for any remaining files
    rem = run("git status --porcelain")
    if rem:
        print("\nNotice - remaining untracked / uncommitted files:")
        print(rem)
        print("Committing remaining files in final maintenance commit...")
        run("git add .")
        run("git commit -m \"chore(repo): finalize repository structure and verification scripts\"")
    
    count = int(run("git rev-list --count HEAD"))
    print(f"\n=======================================================")
    print(f"SUCCESS: Total commits created in repository: {count}")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
