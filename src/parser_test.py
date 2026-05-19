
from pathlib import Path

from rdflib import Graph
import json
from shacl_parser import parse_shacl


BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "data" / "exampleTest.json"
# Load the SHACL file
graph = Graph()
graph.parse("src/data/exampleTest.ttl", format="turtle")
#jsonld = graph.serialize(format="json-ld", indent=2)
jsonld = parse_shacl(graph)




print(jsonld)