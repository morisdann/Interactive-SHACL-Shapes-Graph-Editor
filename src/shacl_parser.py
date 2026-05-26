import json
from pathlib import Path
from urllib.parse import urlparse

from rdflib import BNode, Graph, RDF, Literal, Namespace, URIRef
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



def parse_shacl(graph):
    shapes = []
    for shape in graph.subjects(RDF.type, SH.NodeShape):
        shape_data = {
            "id": str(shape),
            "targetClass": [
                str(target) for target in graph.objects(shape, SH.targetClass)
            ],
            "closed": None,
            "ignoredProperties": [],
            "properties": []
        }

        closed = next(graph.objects(shape, SH.closed), None)
        if closed is not None:
            shape_data["closed"] = str(closed).lower() == "true"

        for ignored_list in graph.objects(shape, SH.ignoredProperties):
            for item in graph.items(ignored_list):
                shape_data["ignoredProperties"].append(str(item))

        for prop in graph.objects(shape, SH.property):
            prop_data = {
                "path": str(next(graph.objects(prop, SH.path), "")),
                "datatype": str(next(graph.objects(prop, SH.datatype), "")),
                "class": str(next(graph.objects(prop, SH["class"]), "")),
                "nodeKind": str(next(graph.objects(prop, SH.nodeKind), "")),
                "minCount": None,
                "maxCount": None,
                "pattern": str(next(graph.objects(prop, SH.pattern), ""))
            }

            min_count = next(graph.objects(prop, SH.minCount), None)
            max_count = next(graph.objects(prop, SH.maxCount), None)

            if min_count is not None:
                prop_data["minCount"] = int(min_count)

            if max_count is not None:
                prop_data["maxCount"] = int(max_count)

            shape_data["properties"].append(prop_data)

        shapes.append(shape_data)


    output_path_json.parent.mkdir(parents=True, exist_ok=True)
    with open("data/exampleTest.json", "w", encoding="utf-8") as f:
        json.dump(shapes, f, indent=2, ensure_ascii=False) 
    print(f"JSON saved to {output_path_json}")
    return shapes


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
    

def bind_namespaces(graph, detected_namespaces):
    # First bind detected custom namespaces
    for namespace_uri, prefix in detected_namespaces.items():
        if namespace_uri not in STANDARD_NAMESPACES:
            graph.bind(prefix, Namespace(namespace_uri), replace=True)

    # Then force standard namespaces
    for namespace_uri, prefix in STANDARD_NAMESPACES.items():
        graph.bind(prefix, Namespace(namespace_uri), replace=True)



def collect_namespaces(shapes_data):
    """
    Scan JSON data and collect all unique namespaces.
    
    Returns:
        dict: {namespace_uri: prefix}
    """
    
    namespaces = dict(STANDARD_NAMESPACES)
    
    # IRIs to scan
    iris_to_check = []
    
    # Collect all IRIs from JSON
    for shape in shapes_data:
        iris_to_check.append(shape.get('id', ''))
        iris_to_check.extend(shape.get('targetClass', []))
        
        for prop in shape.get('properties', []):
            iris_to_check.append(prop.get('path', ''))
            iris_to_check.append(prop.get('datatype', ''))
            iris_to_check.append(prop.get('class', ''))
            iris_to_check.append(prop.get('nodeKind', ''))
        
        iris_to_check.extend(shape.get('ignoredProperties', []))
    
    # Extract namespaces
    for iri in iris_to_check:
        if iri:
            namespace, prefix = extract_namespace(iri)
            if namespace and namespace not in namespaces:
                # Generate unique prefix if conflict
                base_prefix = prefix or 'ex'
                counter = 1
                final_prefix = base_prefix
                while final_prefix in namespaces.values():
                    final_prefix = f"{base_prefix}{counter}"
                    counter += 1
                
                namespaces[namespace] = final_prefix
    
    return namespaces



def _create_rdf_list(graph, items):
    
    if not items:
        return RDF.nil
    
    # Build list from end to beginning
    current = RDF.nil
    for item in reversed(items):
        list_node = BNode()  # Use blank node instead of ugly URN
        graph.add((list_node, RDF.first, URIRef(item) if isinstance(item, str) else Literal(item)))
        graph.add((list_node, RDF.rest, current))
        current = list_node
    
    return current




def parse_json(shapes_data, output_filepath):
    """
    Convert JSON shapes to SHACL RDF format with auto-detected namespaces.
    Uses blank nodes for property shapes and proper RDF list syntax.
    
    Args:
        json_filepath: Path to JSON file with shapes
        output_filepath: Path to output SHACL file (Turtle format)
    
    Returns:
        rdflib.Graph object
    """
    
    # Create RDF graph
    graph = Graph()
    
    # Auto-detect and collect namespaces
    namespaces = collect_namespaces(shapes_data)
    
    # Bind all detected namespaces
    for namespace_uri, prefix in namespaces.items():
        bind_namespaces(graph, namespaces)
    
    print(f"Detected {len(namespaces)} namespaces:")
    for ns_uri, prefix in namespaces.items():
        print(f"  {prefix}: {ns_uri}")
    
    # Process each shape
    for shape_json in shapes_data:
        shape_iri = URIRef(shape_json.get('id', 'http://example.org/UnnamedShape'))
        
        # Add shape type
        graph.add((shape_iri, RDF.type, SH.NodeShape))
        
        # Add targetClass
        for target_class in shape_json.get('targetClass', []):
            if target_class:
                graph.add((shape_iri, SH.targetClass, URIRef(target_class)))
        
        # Add closed constraint
        if shape_json.get('closed') is not None:
            graph.add((shape_iri, SH.closed, Literal(shape_json['closed'])))
        
        # Add ignoredProperties as RDF list
        if shape_json.get('ignoredProperties'):
            ignored_list = _create_rdf_list(graph, shape_json['ignoredProperties'])
            graph.add((shape_iri, SH.ignoredProperties, ignored_list))
        
        # Add properties using BLANK NODES (more idiomatic SHACL)
        for prop_json in shape_json.get('properties', []):
            # Use blank node instead of named URI
            prop_iri = BNode()
            
            # Link property to shape
            graph.add((shape_iri, SH.property, prop_iri))
            
            # Add path
            path = prop_json.get('path', '')
            if path:
                graph.add((prop_iri, SH.path, URIRef(path)))
            
            # Add datatype
            datatype = prop_json.get('datatype', '')
            if datatype:
                graph.add((prop_iri, SH.datatype, URIRef(datatype)))
            
            # Add class
            sh_class = prop_json.get('class', '')
            if sh_class:
                graph.add((prop_iri, SH["class"], URIRef(sh_class)))
            
            # Add nodeKind
            nodeKind = prop_json.get('nodeKind', '')
            if nodeKind:
                graph.add((prop_iri, SH.nodeKind, URIRef(nodeKind)))
            
            # Add minCount
            if prop_json.get('minCount') is not None:
                graph.add((prop_iri, SH.minCount, Literal(prop_json['minCount'])))
            
            # Add maxCount
            if prop_json.get('maxCount') is not None:
                graph.add((prop_iri, SH.maxCount, Literal(prop_json['maxCount'])))
            
            # Add pattern
            pattern = prop_json.get('pattern', '')
            if pattern:
                graph.add((prop_iri, SH.pattern, Literal(pattern)))
    
    # Write to file
    output_path = Path(output_filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(output_path), format='turtle')
    print(f"\nSHACL saved to {output_filepath}")
    
    return graph


"""def roundtrip_test(json_path, shacl_output_path):

    Test the JSON to SHACL conversion.
  
    
    print(f"Converting {json_path} to SHACL...\n")
    graph = parse_json(json_path, shacl_output_path)
    
    print(f"\nGenerated SHACL graph has {len(graph)} triples")"""