# The Eautonome Ontology

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21894601.svg)](https://doi.org/10.5281/zenodo.21894601)

The Eautonome Ontology is an OWL ontology for residential water end-use monitoring. It was developed within the Eautonome greywater monitoring system of the OPUR programme at LEESU, ENPC, Institut Polytechnique de Paris.

The ontology reuses SOSA/SSN for the representation of observations and ETSI SAREF4WATR for water-domain terminology. It aligns the two vocabularies at the class level and extends them with concepts for household end-use attribution, including measurement points, rooms, pipe configurations, and consumption events.

## Persistent identifiers

The ontology is published under the persistent `w3id.org` namespace with HTTP content negotiation.

* Namespace and documentation: https://w3id.org/eautonome/
* Turtle: https://w3id.org/eautonome/eautonome.ttl
* RDF/XML: https://w3id.org/eautonome/eautonome.rdf
* JSON-LD: https://w3id.org/eautonome/eautonome.jsonld
* N-Triples: https://w3id.org/eautonome/eautonome.nt
* DOI (Zenodo): https://doi.org/10.5281/zenodo.21894601

## Contents

The repository contains:

* The ontology schema (T-box) in Turtle, RDF/XML, JSON-LD, and N-Triples
* Two example observation datasets (A-box) in JSON-LD, covering a shower experiment and a hydrodynamic experiment
* SHACL shapes for data validation (`eautonome-shapes.ttl`)

## Reused vocabularies

The ontology reuses or references the following vocabularies:

* W3C SOSA/SSN
* ETSI SAREF4WATR 
* OWL-Time
* QUDT
* schema.org

## Validation

The ontology is defined in OWL 2 DL and was validated using ROBOT. Its consistency was checked with the HermiT reasoner.

The example datasets were validated against seven SHACL shapes and conform to the published SHACL constraints.

The SHACL validation can be reproduced using pySHACL:

```bash
pip install pyshacl
pyshacl -s eautonome-shapes.ttl -d eautonome.ttl -df turtle
```

## Publication

The ontology is published through a GitHub Pages deployment using the persistent `w3id.org/eautonome/` namespace. HTTP content negotiation provides access to the ontology in the requested RDF serialization based on the HTTP `Accept` header.

The ontology was also included in the implementation report associated with the 2023 edition of the W3C SSN/SOSA recommendation.

## Citation

Önal, E. (2026). *The Eautonome Ontology* (Version 1.0.0). Zenodo. https://doi.org/10.5281/zenodo.21894601

## License

This ontology is released under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

## Contact

Erdem Önal
LEESU, ENPC, Institut Polytechnique de Paris
erdem.onal [at] enpc.fr
