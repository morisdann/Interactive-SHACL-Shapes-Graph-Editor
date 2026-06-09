import json
from pathlib import Path
from urllib.parse import urlparse

from rdflib import XSD, BNode, Graph, RDF, Literal, Namespace, URIRef
from rdflib.namespace import SH


BASE_DIR = Path(__file__).resolve().parent
output_path_json = BASE_DIR / "data" / "exampleTest.json"
output_path_shacl = BASE_DIR/ "data" / "exampleTestShacl.ttl"

# Standard well-known namespaces
STANDARD_NAMESPACES = {
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/ns/shacl#": "sh",
    "http://example.com/ns#": "ex"
}



from rdflib import RDF
from rdflib.namespace import SH


def local_name(value):
    value = str(value)

    if "#" in value:
        return value.rsplit("#", 1)[1]

    if "/" in value:
        return value.rstrip("/").rsplit("/", 1)[1]

    return value


def shorten_uri(graph, value):
    """
    Convert full URI to prefixed form if possible.
    Example:
    http://example.com/ns#Person -> ex:Person
    http://www.w3.org/ns/shacl#IRI -> sh:IRI
    """
    try:
        return graph.namespace_manager.normalizeUri(value)
    except Exception:
        return str(value)


def make_constraint(counter, predicate_name, value):
    counter["constraint"] += 1

    short_value = value

    return {
        "id": f"constraint-{counter['constraint']}",
        "type": "Constraint",
        "label": f"{predicate_name.split(':')[-1]} = {short_value}",
        "properties": {
            predicate_name: short_value
        },
        "children": []
    }

ALWAYS_KEEP_PREFIXES = {"rdf", "rdfs", "sh", "xsd"}


def get_namespaces_from_graph(graph):
    used_namespace_uris = set()

    def collect_from_term(term):
        if not isinstance(term, URIRef):
            return

        iri = str(term)

        if "#" in iri:
            used_namespace_uris.add(iri.rsplit("#", 1)[0] + "#")
        elif "/" in iri:
            used_namespace_uris.add(iri.rsplit("/", 1)[0] + "/")

    for subject, predicate, obj in graph:
        collect_from_term(subject)
        collect_from_term(predicate)
        collect_from_term(obj)

    namespaces = {}

    for prefix, namespace in graph.namespaces():
        namespace_uri = str(namespace)

        if namespace_uri in used_namespace_uris or prefix in ALWAYS_KEEP_PREFIXES:
            namespaces[prefix] = namespace_uri

    return namespaces

def parse_shacl(graph):
    trees = []

    counter = {
        "shape": 0,
        "property": 0,
        "constraint": 0,
        "logical": 0
    }

    for shape in graph.subjects(RDF.type, SH.NodeShape):
        counter["shape"] += 1

        shape_node = {
            "id": f"shape-{counter['shape']}",
            "type": "NodeShape",
            "label": local_name(shape),
            "properties":{
                "rdf:about": shorten_uri(graph, shape)
            },
            "children": []
        }

        target_classes = [
            shorten_uri(graph, target)
            for target in graph.objects(shape, SH.targetClass)
        ]

        if len(target_classes) == 1:
            shape_node["properties"]["sh:targetClass"] = target_classes[0]
        elif len(target_classes) > 1:
            shape_node["properties"]["sh:targetClass"] = target_classes

        closed = next(graph.objects(shape, SH.closed), None)
        if closed is not None:
            shape_node["properties"]["sh:closed"] = str(closed).lower() == "true"

        ignored_properties = []

        for ignored_list in graph.objects(shape, SH.ignoredProperties):
            for item in graph.items(ignored_list):
                ignored_properties.append(shorten_uri(graph, item))

        if ignored_properties:
            shape_node["properties"]["sh:ignoredProperties"] = ignored_properties

        for prop in graph.objects(shape, SH.property):
            counter["property"] += 1

            path = next(graph.objects(prop, SH.path), None)
            path_value = shorten_uri(graph, path) if path else ""

            prop_node = {
                "id": f"prop-{counter['property']}",
                "type": "PropertyShape",
                "label": f"{local_name(path) if path else 'unknown'} property",
                "properties": {},
                "children": []
            }

            if path:
                prop_node["properties"]["sh:path"] = path_value

            constraint_predicates = [
                (SH.minCount, "sh:minCount", int),
                (SH.maxCount, "sh:maxCount", int),
                (SH.datatype, "sh:datatype", None),
                (SH["class"], "sh:class", None),
                (SH.nodeKind, "sh:nodeKind", None),
                (SH.node, "sh:node", None),
                (SH.pattern, "sh:pattern", str),

            ]

            for predicate_uri, predicate_name, converter in constraint_predicates:
                value = next(graph.objects(prop, predicate_uri), None)

                if value is None:
                    continue

                if converter is int:
                    parsed_value = int(value)
                elif converter is str:
                    parsed_value = str(value)
                else:
                    parsed_value = shorten_uri(graph, value)

                prop_node["children"].append(
                    make_constraint(counter, predicate_name, parsed_value)
                )

            shape_node["children"].append(prop_node)

        trees.append(shape_node)
    result = {
    "namespaces": get_namespaces_from_graph(graph)
    }

    if len(trees) == 1:
        result["tree"] = trees[0]
    else:
        result["trees"] = trees

    output_path_json.parent.mkdir(parents=True, exist_ok=True)

    with output_path_json.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"JSON saved to {output_path_json}")

    return result
    



def get_tree_data(data):
    if isinstance(data, str):
        data = json.loads(data)

    namespaces = data.get("namespaces", {}) if isinstance(data, dict) else {}

    if isinstance(data, dict) and "tree" in data:
        return [data["tree"]], namespaces

    if isinstance(data, dict) and "trees" in data:
        return data["trees"], namespaces

    if isinstance(data, list):
        return data, {}

    raise ValueError("Expected contract JSON with 'tree' or 'trees'")

def extract_namespace(iri_string):
    """
    Extract namespace from an IRI.
    Handles both # and / separators.
    """
    
    if not iri_string or iri_string == "":
        return None, None
    
    try:
        parsed = urlparse(iri_string)
    except:
        return None, None
    
    # Find the last # or / to determine namespace boundary
    if '#' in iri_string:
        namespace = iri_string.rsplit('#', 1)[0] + '#'
        local_name = iri_string.rsplit('#', 1)[1]
    else:
        parts = iri_string.rsplit('/', 1)
        if len(parts) == 2 and '://' in iri_string:
            namespace = parts[0] + '/'
            local_name = parts[1]
        else:
            return None, None
    
    # Check if it's a standard namespace first
    if namespace in STANDARD_NAMESPACES:
        return namespace, STANDARD_NAMESPACES[namespace]
    
    # Generate prefix from domain
    try:
        domain = parsed.netloc.split('.')
        prefix = domain[-2] if len(domain) > 1 else domain[0]  # e.g., "example" from "example.com"
        return namespace, prefix
    except:
        return None, None


def bind_prefix_namespaces(graph, namespaces):
    # namespaces is prefix -> namespace URI
    for prefix, namespace_uri in namespaces.items():
        graph.bind(prefix, Namespace(namespace_uri), replace=True)

    # force standards
    for namespace_uri, prefix in STANDARD_NAMESPACES.items():
        graph.bind(prefix, Namespace(namespace_uri), replace=True)




def expand_prefixes(value, namespaces):
    if not isinstance(value, str):
        return value

    if value.startswith(("http://", "https://", "urn:")):
        return value

    if ":" not in value:
        return value

    prefix, local = value.split(":", 1)

    namespace_uri = namespaces.get(prefix)

    if namespace_uri:
        return namespace_uri + local

    return value





def _create_rdf_list(graph, items):
    if not items:
        return RDF.nil

    current = RDF.nil

    for item in reversed(items):
        list_node = BNode()

        if isinstance(item, (URIRef, Literal, BNode)):
            rdf_item = item
        elif isinstance(item, str):
            rdf_item = URIRef(item) if item.startswith(("http://", "https://", "urn:")) else Literal(item)
        else:
            rdf_item = Literal(item)

        graph.add((list_node, RDF.first, rdf_item))
        graph.add((list_node, RDF.rest, current))

        current = list_node

    return current


SHACL_PREDICATES = {
    "sh:targetClass": SH.targetClass,
    "sh:closed": SH.closed,
    "sh:ignoredProperties": SH.ignoredProperties,
    "sh:path": SH.path,
    "sh:minCount": SH.minCount,
    "sh:maxCount": SH.maxCount,
    "sh:datatype": SH.datatype,
    "sh:class": SH["class"],
    "sh:nodeKind": SH.nodeKind,
     "sh:node": SH.node,
    "sh:pattern": SH.pattern,
}


def to_rdf_value(value,namespaces):
    value = expand_prefixes(value, namespaces)

    if isinstance(value, bool):
        return Literal(value, datatype=XSD.boolean)

    if isinstance(value, int):
        return Literal(value, datatype=XSD.integer)

    if isinstance(value, str):
        if value.startswith(("http://", "https://", "urn:")):
            return URIRef(value)

        return Literal(value)

    return Literal(value)

def standard_prefix_map():
    return {
        prefix: namespace_uri
        for namespace_uri, prefix in STANDARD_NAMESPACES.items()
    }


def parse_json(tree_data, output_filepath):
    root_nodes, json_namespaces = get_tree_data(tree_data)

    graph = Graph()
    namespaces = {
        prefix: namespace_uri
        for namespace_uri, prefix in STANDARD_NAMESPACES.items()
    }
    namespaces.update(json_namespaces)

    bind_prefix_namespaces(graph, namespaces)

    print(f"Detected {len(namespaces)} namespaces:")
    for ns_uri, prefix in namespaces.items():
        print(f"  {prefix}: {ns_uri}")

    def add_constraint(parent_node, constraint_node):
        for pred_name, value in constraint_node.get("properties", {}).items():
            pred_uri = SHACL_PREDICATES.get(pred_name)

            if pred_uri is None:
                continue

            graph.add((parent_node, pred_uri, to_rdf_value(value,namespaces)))

    def add_property_shape(parent_shape_iri, prop_node):
        prop_bnode = BNode()
        graph.add((parent_shape_iri, SH.property, prop_bnode))

        for pred_name, value in prop_node.get("properties", {}).items():
            pred_uri = SHACL_PREDICATES.get(pred_name)

            if pred_uri is None:
                continue

            graph.add((prop_bnode, pred_uri, to_rdf_value(value,namespaces)))

        for child in prop_node.get("children", []):
            if child.get("type") == "Constraint":
                add_constraint(prop_bnode, child)

            elif child.get("type") == "LogicalOperator":
                # Not implemented yet
                pass

        return prop_bnode

    for root in root_nodes:
        if root.get("type") != "NodeShape":
            raise ValueError(f"Root node must be NodeShape, got {root.get('type')}")

        shape_ref = root.get("properties", {}).get("rdf:about")

        if shape_ref:
            shape_iri = URIRef(expand_prefixes(shape_ref,namespaces))
        else:
            shape_label = root.get("label") or root.get("id")
            shape_iri = URIRef(f"http://example.com/ns#{shape_label}")

        graph.add((shape_iri, RDF.type, SH.NodeShape))

        for pred_name, value in root.get("properties", {}).items():
            pred_uri = SHACL_PREDICATES.get(pred_name)

            if pred_uri is None:
                continue

            if pred_name == "sh:ignoredProperties":
                items = [to_rdf_value(item, namespaces) for item in value]
                ignored_list = _create_rdf_list(graph, items)
                graph.add((shape_iri, SH.ignoredProperties, ignored_list))
            else:
                graph.add((shape_iri, pred_uri, to_rdf_value(value, namespaces)))

        for child in root.get("children", []):
            if child.get("type") == "PropertyShape":
                add_property_shape(shape_iri, child)

            elif child.get("type") == "Constraint":
                add_constraint(shape_iri, child)

            elif child.get("type") == "LogicalOperator":
                # Not implemented yet
                pass

    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    graph.serialize(destination=str(output_path), format="turtle")

    print(f"\nSHACL saved to {output_filepath}")

    return graph



