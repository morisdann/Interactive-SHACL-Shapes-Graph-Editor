
from pathlib import Path

from rdflib import Graph
import json
from backend.shacl_parser import parse_shacl, parse_json 


BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "data" / "exampleTest.json"
# Load the SHACL file
graph = Graph()
graph.parse("src/data/schema1.ttl", format="turtle")

jsonld = parse_shacl(graph)



with open(BASE_DIR / "data" / "exampleTest.json", 'r', encoding='utf-8') as f:
        shapes_data = json.load(f)
parse_json(shapes_data, "data/output.ttl")

graph2 = Graph()
graph2.parse("src/data/output.ttl", format="turtle")
print(graph.isomorphic(graph2))
