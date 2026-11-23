"""
DBLP Discovery Dataset (D3) Streaming & Subsetting Module
Streams JSONL records from Hugging Face without downloading the full 15.76 GB file.
Extracts an AI/Machine Learning research subset (2016-2025).
Excludes author emails by design.
"""

import os
import json
import re
import urllib.request
from typing import Dict, Any, List, Optional, Tuple

D3_URL = "https://huggingface.co/datasets/jpwahle/dblp-discovery-dataset/resolve/main/papers/papers-00000-of-00001.jsonl"
USER_AGENT = "ResearchKG-AcademicBot/1.0 (academic research at university; non-commercial)"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

AIML_KEYWORDS = [
    "machine learning", "deep learning", "neural network", "graph neural network",
    "knowledge graph", "artificial intelligence", "reinforcement learning",
    "computer vision", "natural language processing", "representation learning",
    "graph representation", "supervised learning", "unsupervised learning",
    "convolutional", "transformer", "semantic web", "ontology"
]

def is_aiml_paper(record: Dict[str, Any], min_year: int = 2016, max_year: int = 2025) -> Tuple[bool, str]:
    """
    Evaluates whether a paper belongs to the CS AI/ML working scope.
    Checks year, s2fieldsofstudy, CSO topics (enhanced/semantic), and title/abstract keywords.
    Returns (is_match, reason).
    """
    year = record.get("year")
    if not year or year < min_year or year > max_year:
        return False, "Year out of range"
        
    # Check CS domain in s2fieldsofstudy
    fos_list = record.get("s2fieldsofstudy") or []
    has_cs = any(isinstance(f, dict) and f.get("category") == "Computer Science" for f in fos_list)
    
    # Check CSO ontology concepts
    enhanced = [str(x).lower() for x in record.get("enhanced") or []]
    semantic = [str(x).lower() for x in record.get("semantic") or []]
    cso_topics = set(enhanced + semantic)
    
    for kw in AIML_KEYWORDS:
        if any(kw in topic for topic in cso_topics):
            return True, f"CSO topic match: {kw}"

    # Check title text
    title = (record.get("title") or "").lower()
    for kw in AIML_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', title):
            return True, f"Title keyword match: {kw}"

    # Check abstract if CS domain confirmed
    if has_cs:
        abstract = (record.get("abstract") or "").lower()
        for kw in AIML_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', abstract):
                return True, f"Abstract keyword match: {kw}"

    return False, "No AI/ML match"

def stream_d3_subset(target_count: int = 100, 
                     min_year: int = 2016, 
                     max_year: int = 2025,
                     save_raw_snapshot: bool = True) -> List[Dict[str, Any]]:
    """
    Streams JSONL records from Hugging Face line by line.
    Applies filtering on the fly and saves the snapshot.
    """
    print("=" * 70)
    print(f"STREAMING DBLP DISCOVERY DATASET (D3) FROM HUGGING FACE")
    print(f"Target count: {target_count} | Year range: {min_year}-{max_year}")
    print(f"URL: {D3_URL}")
    print("=" * 70)

    req = urllib.request.Request(D3_URL, headers={"User-Agent": USER_AGENT})
    
    matched_papers = []
    scanned_count = 0
    match_reasons = {}

    with urllib.request.urlopen(req, timeout=30) as response:
        buffer = ""
        while len(matched_papers) < target_count:
            chunk = response.read(65536) # read 64 KB chunks
            if not chunk:
                print("End of stream reached.")
                break
                
            buffer += chunk.decode("utf-8", errors="replace")
            lines = buffer.split("\n")
            # keep the last incomplete line in buffer
            buffer = lines.pop()

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                scanned_count += 1
                try:
                    record = json.loads(line)
                    is_match, reason = is_aiml_paper(record, min_year, max_year)
                    if is_match:
                        # Sanitize author records: ensure email is EXCLUDED
                        sanitized_authors = []
                        for a in record.get("authors") or []:
                            sanitized_authors.append({
                                "authorId": str(a.get("authorId", "")),
                                "name": a.get("name", "").strip()
                            })
                            
                        sanitized_record = {
                            "corpusid": record.get("corpusid"),
                            "externalids": record.get("externalids") or {},
                            "title": (record.get("title") or "").strip(),
                            "abstract": (record.get("abstract") or "").strip(),
                            "year": record.get("year"),
                            "venue": (record.get("venue") or "").strip(),
                            "citationcount": record.get("citationcount", 0),
                            "referencecount": record.get("referencecount", 0),
                            "authors": sanitized_authors,
                            "cso_enhanced": record.get("enhanced") or [],
                            "cso_semantic": record.get("semantic") or [],
                            "s2fieldsofstudy": record.get("s2fieldsofstudy") or []
                        }
                        matched_papers.append(sanitized_record)
                        match_reasons[reason] = match_reasons.get(reason, 0) + 1
                        
                        if len(matched_papers) % 20 == 0 or len(matched_papers) == target_count:
                            print(f"[Stream Progress] Scanned: {scanned_count:,} | Matched: {len(matched_papers)}/{target_count}")
                            
                        if len(matched_papers) >= target_count:
                            break
                except json.JSONDecodeError:
                    continue

    print(f"\nStream Completed: Scanned {scanned_count:,} records to extract {len(matched_papers)} matching papers.")
    print("Match Reason Distribution:")
    for r, count in sorted(match_reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {r}: {count}")

    if save_raw_snapshot:
        snapshot_filename = f"d3_raw_snapshot_{len(matched_papers)}.json"
        snapshot_path = os.path.join(DATA_RAW_DIR, snapshot_filename)
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(matched_papers, f, indent=2)
        print(f"[Snapshot] Saved {len(matched_papers)} raw D3 records to: {snapshot_path}")

    return matched_papers

if __name__ == "__main__":
    stream_d3_subset(target_count=100)
