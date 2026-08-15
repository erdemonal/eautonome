#!/usr/bin/env python3
import csv
import sys
from pathlib import Path
from rdflib import Graph

if len(sys.argv) != 4:
    raise SystemExit("usage: run_queries.py eautonome.ttl hydrodynamic-observations.jsonld shower-observations.jsonld")

root = Path(__file__).resolve().parent
graph = Graph()
graph.parse(sys.argv[1], format="turtle")
graph.parse(sys.argv[2], format="json-ld")
graph.parse(sys.argv[3], format="json-ld")

expected = {}
with (root / "expected-results.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        expected[row["query"]] = int(row["expected_rows"])

failed = False
for i in range(1, 14):
    qid = f"Q{i}"
    query = (root / "queries" / f"q{i:02d}.rq").read_text(encoding="utf-8")
    count = len(list(graph.query(query)))
    target = expected[qid]
    print(f"{qid}: {count} rows (expected {target})")
    if count != target:
        failed = True

raise SystemExit(1 if failed else 0)
