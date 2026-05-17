from rdflib import Graph, Namespace

from shacl_parser import extract_all_shapes


# Load the SHACL file
graph = Graph()
graph.parse("src/data/exampleTest.ttl", format="turtle")


print(extract_all_shapes(graph))