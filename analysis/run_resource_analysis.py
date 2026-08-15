#!/usr/bin/env python3
"""Reproduce the Eautonome ablation and sensor coverage analyses.

Usage:
  python analysis/run_resource_analysis.py \
      docs/ontology/eautonome.ttl \
      docs/data/hydrodynamic-observations.jsonld \
      docs/data/shower-observations.jsonld \
      queries

The script runs queries q01 to q13 on the complete graph and on a
modified copy of the graph. In the modified graph, instance statements
that use properties defined in Eautonome are removed. It also removes
rdf:type statements that assign individuals to Eautonome classes.

The ontology schema, class alignments, and statements that use reused
vocabularies are kept.

The script also reports sensor coverage at each measurement point and
descriptive statistics for the hydrodynamic observation collections.
The hydrodynamic statistics are descriptive and are not used to estimate
an effect of pipe configuration.
"""

from __future__ import annotations

import csv
import statistics
import sys
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, OWL, RDF

EAU = Namespace("https://w3id.org/eautonome/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
TIME = Namespace("http://www.w3.org/2006/time#")


def local(term) -> str:
    text = str(term)
    return text.rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def load_graph(ontology: Path, hydro: Path, shower: Path) -> tuple[Graph, Graph]:
    schema = Graph()
    schema.parse(ontology, format="turtle")
    graph = Graph()
    graph += schema
    graph.parse(hydro, format="json-ld")
    graph.parse(shower, format="json-ld")
    return schema, graph


def eautonome_terms(schema: Graph):
    classes = {
        s for s in schema.subjects(RDF.type, OWL.Class)
        if str(s).startswith(str(EAU))
    }
    properties = {
        s for typ in (OWL.ObjectProperty, OWL.DatatypeProperty)
        for s in schema.subjects(RDF.type, typ)
        if str(s).startswith(str(EAU))
    }
    return classes, properties


def assertion_ablation(graph: Graph, classes, properties) -> Graph:
    """Remove Eautonome-specific data assertions, retaining the schema.

    Removed triples are either (1) assertions whose predicate is an
    Eautonome-defined object/datatype property or (2) rdf:type assertions
    to an Eautonome-defined class. Schema axioms are retained, making this
    a conservative ablation of instance-level extension assertions.
    """
    out = Graph()
    for s, p, o in graph:
        if p in properties:
            continue
        if p == RDF.type and o in classes:
            continue
        out.add((s, p, o))
    return out


def query_counts(graph: Graph, query_dir: Path):
    counts = {}
    for i in range(1, 14):
        qid = f"Q{i}"
        query = (query_dir / f"q{i:02d}.rq").read_text(encoding="utf-8")
        counts[qid] = len(list(graph.query(query)))
    return counts


def coverage_rows(graph: Graph):
    query = """
PREFIX eau: <https://w3id.org/eautonome/>
SELECT ?mp ?room ?waterKind
       (COUNT(DISTINCT ?sensor) AS ?sensorCount)
       (SUM(IF(?status = "active", 1, 0)) AS ?activeSensorCount)
WHERE {
  ?mp a eau:MeasurementPoint ;
      eau:locatedIn ?room ;
      eau:measuresWaterKind ?waterKind .
  ?sensor eau:monitors ?mp ;
          eau:hasOperationalStatus ?status .
}
GROUP BY ?mp ?room ?waterKind
ORDER BY ?mp
"""
    rows = []
    for mp, room, water_kind, sensor_count, active_count in graph.query(query):
        rows.append({
            "measurement_point": local(mp),
            "room": local(room),
            "water_kind": local(water_kind),
            "sensor_count": int(sensor_count),
            "active_sensor_count": int(active_count),
        })
    return rows


def hydrodynamic_rows(graph: Graph):
    collections = []
    for collection in graph.subjects(RDF.type, SOSA.ObservationCollection):
        config = graph.value(collection, EAU.hasPipeConfiguration)
        if config is None:
            continue
        members = list(graph.objects(collection, SOSA.hasMember))
        values = [float(graph.value(obs, SOSA.hasSimpleResult)) for obs in members]
        interval = graph.value(collection, SOSA.phenomenonTime)
        beginning = graph.value(graph.value(interval, TIME.hasBeginning), TIME.inXSDDateTime)
        end = graph.value(graph.value(interval, TIME.hasEnd), TIME.inXSDDateTime)
        duration = None
        if beginning is not None and end is not None:
            duration = (end.toPython() - beginning.toPython()).total_seconds()
        collections.append({
            "collection": local(collection),
            "configuration": local(config),
            "n": len(values),
            "duration_s": duration,
            "mean_l_min": statistics.mean(values),
            "median_l_min": statistics.median(values),
            "min_l_min": min(values),
            "max_l_min": max(values),
        })
    return sorted(collections, key=lambda row: row["collection"])


def write_csv(path: Path, fieldnames: Iterable[str], rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    ontology, hydro, shower, query_dir = map(Path, sys.argv[1:])
    schema, full = load_graph(ontology, hydro, shower)
    classes, properties = eautonome_terms(schema)
    ablated = assertion_ablation(full, classes, properties)

    full_counts = query_counts(full, query_dir)
    ablated_counts = query_counts(ablated, query_dir)
    ablation_rows = [
        {
            "query": qid,
            "full_count": full_counts[qid],
            "ablated_count": ablated_counts[qid],
            "retention_percent": round(100 * ablated_counts[qid] / full_counts[qid], 1)
            if full_counts[qid] else 0.0,
        }
        for qid in full_counts
    ]

    coverage = coverage_rows(full)
    hydro_stats = hydrodynamic_rows(full)

    unchanged = sum(r["full_count"] == r["ablated_count"] for r in ablation_rows)
    zeroed = sum(r["full_count"] > 0 and r["ablated_count"] == 0 for r in ablation_rows)
    no_active = [r for r in coverage if r["active_sensor_count"] == 0]
    redundant_active = [r for r in coverage if r["active_sensor_count"] > 1]
    treated = [r for r in coverage if r["water_kind"] == "TreatedGreywater"]
    treated_uncovered = [r for r in treated if r["active_sensor_count"] == 0]

    print("Ablation summary")
    print(f"  Queries with unchanged answer counts: {unchanged}/13")
    print(f"  Queries reduced to zero answers:      {zeroed}/13")
    print(f"  Q10 deployment sensors:               {full_counts['Q10']} -> {ablated_counts['Q10']}")
    print("\nPer-query counts")
    for row in ablation_rows:
        print(f"  {row['query']:>3}: {row['full_count']:>4} -> {row['ablated_count']:>4} ({row['retention_percent']:>5.1f}%)")

    print("\nMonitoring coverage")
    print(f"  Measurement points:                   {len(coverage)}")
    print(f"  No active sensor:                     {len(no_active)}")
    print(f"  More than one active sensor:          {len(redundant_active)}")
    print(f"  Treated-graywater points:             {len(treated)}")
    print(f"  Treated-graywater points uncovered:   {len(treated_uncovered)}")
    for row in coverage:
        print(
            f"  {row['measurement_point']}: active {row['active_sensor_count']}/"
            f"{row['sensor_count']}, {row['water_kind']}"
        )

    print("\nHydrodynamic collection statistics (descriptive only)")
    for row in hydro_stats:
        print(
            f"  {row['collection']} [{row['configuration']}]: n={row['n']}, "
            f"duration={row['duration_s']:.0f}s, mean={row['mean_l_min']:.3f}, "
            f"median={row['median_l_min']:.3f}, range={row['min_l_min']:.2f}-{row['max_l_min']:.2f} L/min"
        )

    outdir = Path(__file__).resolve().parent
    write_csv(outdir / "ablation-results.csv", ablation_rows[0].keys(), ablation_rows)
    write_csv(outdir / "coverage-results.csv", coverage[0].keys(), coverage)
    write_csv(outdir / "hydrodynamic-collection-stats.csv", hydro_stats[0].keys(), hydro_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
