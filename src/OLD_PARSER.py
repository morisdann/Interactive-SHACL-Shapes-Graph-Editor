import json
from pathlib import Path

from rdflib import RDF, SH, Graph


BASE_DIR = Path(__file__).resolve().parent
output_path_json = BASE_DIR / "data" / "exampleTest.json"
output_path_shacl = BASE_DIR/ "data" / "exampleTestShacl.ttl"

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