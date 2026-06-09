from pyshacl import validate


def validate_shacl(shapes):
    conforms, results_graph, results_text = validate(
        data_graph="data.ttl",
        shacl_graph="shapes.ttl",
        data_graph_format="turtle",
        shacl_graph_format="turtle"
    )
    return conforms, results_graph, results_text
