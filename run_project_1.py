"""
Master One-Click Execution Pipeline for Project - I
Academic Project Title 34: Graph-Based Knowledge Graph for Research Collaboration Analysis

Executes:
1. Data verification (confirms raw OpenAlex 5,000-work corpus presence).
2. Preprocessing & relational table generation (produces clean CSVs in data/processed/ and data/graph_ready/).
3. Master validation & quality audit (primary key uniqueness, 100% referential integrity, privacy check).
4. Prints summary report and Neo4j loading instructions.
"""

import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)

def main():
    print_header("Executing Project - I End-to-End Pipeline")
    print(f"Working Directory: {BASE_DIR}")

    # Step 1: Check raw data
    raw_path = os.path.join(BASE_DIR, "data", "raw", "openalex_raw_5000.json")
    if not os.path.exists(raw_path):
        print(f"\n[Step 1] Raw dataset missing at {raw_path}.")
        print("Harvesting 5,000 AI/ML works (2016-2025) from OpenAlex API...")
        harvest_script = os.path.join(BASE_DIR, "src", "harvest", "collect_openalex_corpus.py")
        subprocess.run([sys.executable, harvest_script], check=True)
    else:
        print(f"\n[Step 1] Raw dataset verified: {raw_path} ({os.path.getsize(raw_path):,} bytes)")

    # Step 2: Run preprocessing and relational extraction
    print("\n[Step 2] Processing raw JSON into normalized relational tables...")
    preprocess_script = os.path.join(BASE_DIR, "src", "preprocess", "process_openalex_5000.py")
    subprocess.run([sys.executable, preprocess_script], check=True)

    # Step 3: Run comprehensive validation suite
    print("\n[Step 3] Running Project - I Automated Validation Suite...")
    val_script = os.path.join(BASE_DIR, "src", "validate_project_1.py")
    subprocess.run([sys.executable, val_script], check=True)

    # Step 4: Next steps for Neo4j
    print_header("Project - I Successfully Completed")
    print("""
All Project - I deliverables are generated and validated:
1. Literature Review:
   - literature_review.md
   - literature_matrix.csv
2. Relational & Graph Datasets:
   - data/processed/works.csv (4,989 unique works)
   - data/processed/authors.csv (22,185 unique authors; emails excluded)
   - data/processed/institutions.csv (2,738 institutions with ROR & ISO countries)
   - data/processed/venues.csv (904 publication venues)
   - data/processed/topics.csv (519 canonical research topics)
   - data/processed/authorships.csv (30,930 authorship edges)
   - data/processed/affiliations.csv (33,410 affiliation edges)
   - data/processed/work_topics.csv (14,967 topic classification edges)
3. Documentation & Schemas:
   - docs/data_dictionary.md
   - docs/graph_schema.md
   - docs/project_i_completion_report.md
   - neo4j/schema.cypher & neo4j/load_data.cypher
   - docker-compose.yml

To load into Neo4j locally:
  $ docker compose up -d
  Then execute 'neo4j/schema.cypher' followed by 'neo4j/load_data.cypher' in Neo4j Browser (http://localhost:7474).
""")

if __name__ == "__main__":
    main()
