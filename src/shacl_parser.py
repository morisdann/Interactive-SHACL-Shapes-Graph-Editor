import json
from rdflib import Graph, Namespace, RDF, RDFS, URIRef

# Define namespaces
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = Namespace("http://example.org/")


def extract_shape(graph, shape_iri):
    """
    Extract a single shape and all its properties from the RDF graph.
    """
    
    # Convert string to URIRef if needed
    if isinstance(shape_iri, str):
        try:
            shape_iri = URIRef(shape_iri)
        except Exception:
            return None
    
    shape = {
        'id': str(shape_iri),
        'name': get_single_value(graph, shape_iri, RDFS.label),
        'description': get_single_value(graph, shape_iri, RDFS.comment),
        'targetClass': get_all_values(graph, shape_iri, SH.targetClass),
        'targetNode': get_all_values(graph, shape_iri, SH.targetNode),
        'properties': []
    }
    
    # Extract all property shapes
    property_shapes = list(graph.objects(shape_iri, SH.property))
    
    for prop_shape in property_shapes:
        prop_data = extract_property_shape(graph, prop_shape)
        if prop_data:
            shape['properties'].append(prop_data)
    
    return shape


def extract_all_shapes(graph):
    """
    Automatically find and extract all NodeShapes from the graph.
    Discovers shapes from ANY namespace, not just predefined ones.
    """
    all_shapes = []
    
    # Find all IRIs for shapes by querying for rdf:type sh:NodeShape
    shape_iris = list(graph.subjects(RDF.type, SH.NodeShape))
    
    print(f"Found {len(shape_iris)} shapes in the document")
    
    for shape_iri in shape_iris:
        shape = extract_shape(graph, shape_iri)
        if shape:
            all_shapes.append(shape)
    
    return all_shapes


def extract_property_shape(graph, prop_shape_iri):
    """
    Extract a single property shape with all its constraints.
    """
    
    try:
        prop = {
            'id': str(prop_shape_iri),
            'path': get_property_path(graph, prop_shape_iri),
            'name': get_single_value(graph, prop_shape_iri, RDFS.label),
            'description': get_single_value(graph, prop_shape_iri, RDFS.comment),
            'constraints': {}
        }
        
        # Extract common constraints
        constraints = prop['constraints']
        
        # Data type constraint
        datatype = get_single_value(graph, prop_shape_iri, SH.datatype)
        if datatype:
            constraints['datatype'] = datatype
        
        # Class constraint (use SH["class"] for reserved keyword)
        sh_class = get_single_value(graph, prop_shape_iri, SH["class"])
        if sh_class:
            constraints['class'] = sh_class
        
        # Cardinality constraints
        min_count = get_single_value(graph, prop_shape_iri, SH.minCount)
        if min_count:
            try:
                constraints['minCount'] = int(min_count)
            except ValueError:
                pass
        
        max_count = get_single_value(graph, prop_shape_iri, SH.maxCount)
        if max_count:
            try:
                constraints['maxCount'] = int(max_count)
            except ValueError:
                pass
        
        # String length constraints
        min_length = get_single_value(graph, prop_shape_iri, SH.minLength)
        if min_length:
            try:
                constraints['minLength'] = int(min_length)
            except ValueError:
                pass
        
        max_length = get_single_value(graph, prop_shape_iri, SH.maxLength)
        if max_length:
            try:
                constraints['maxLength'] = int(max_length)
            except ValueError:
                pass
        
        # Pattern constraint (regex)
        pattern = get_single_value(graph, prop_shape_iri, SH.pattern)
        if pattern:
            constraints['pattern'] = pattern
        
        # In constraint (use SH["in"] for reserved keyword)
        in_values = get_rdf_list(graph, prop_shape_iri, SH["in"])
        if in_values:
            constraints['in'] = [str(v) for v in in_values]
        
        return prop
    
    except Exception as e:
        print(f"Error extracting property shape {prop_shape_iri}: {e}")
        return None


def get_property_path(graph, prop_shape_iri):
    """
    Extract the sh:path from a property shape.
    Handles simple paths and sequences.
    """
    
    path = graph.value(prop_shape_iri, SH.path)
    
    if not path:
        return None
    
    # Check if it's an RDF list (sequence path)
    first = graph.value(path, RDF.first)
    if first:
        # It's a list - extract all elements
        path_sequence = get_rdf_list(graph, path)
        return {
            'type': 'sequence',
            'paths': [str(p) for p in path_sequence]
        }
    
    # Simple single path
    return {
        'type': 'simple',
        'path': str(path)
    }


def get_rdf_list(graph, list_node, predicate=None):
    """
    Extract an RDF list into a Python list.
    RDF lists use rdf:first and rdf:rest structure.
    """
    
    # If predicate provided, get the list node first
    if predicate:
        list_node = graph.value(list_node, predicate)
    
    if not list_node:
        return []
    
    result = []
    current = list_node
    
    # Traverse the RDF list structure (max 10000 iterations to prevent infinite loops)
    iterations = 0
    while current and current != RDF.nil and iterations < 10000:
        # Get the first element
        first = graph.value(current, RDF.first)
        if first:
            result.append(first)
        
        # Move to next
        current = graph.value(current, RDF.rest)
        iterations += 1
    
    return result


def get_single_value(graph, subject, predicate):
    """
    Get a single value for a predicate.
    Returns None if not found.
    """
    try:
        value = graph.value(subject, predicate)
        return str(value) if value else None
    except Exception:
        return None


def get_all_values(graph, subject, predicate):
    """
    Get all values for a predicate (multiple values possible).
    Returns a list of strings.
    """
    try:
        values = list(graph.objects(subject, predicate))
        return [str(v) for v in values]
    except Exception:
        return []


def parse_shacl_to_json(filepath, output_filepath=None):
    """
    Load a SHACL shapes document and extract all shapes to JSON.
    Works with ANY RDF format (Turtle, RDF/XML, N3, JSON-LD, etc.)
    Automatically discovers all shapes regardless of namespace.
    
    Args:
        filepath: Path to RDF file (Turtle, RDF/XML, etc.)
        output_filepath: Optional - write JSON to file
    
    Returns:
        Dictionary with all shapes
    """
    
    # Load the RDF graph
    graph = Graph()
    try:
        # rdflib auto-detects format, but you can specify if needed
        graph.parse(filepath)
        print(f"Successfully parsed {filepath}")
        print(f"Graph contains {len(graph)} triples")
    except Exception as e:
        print(f"Error parsing RDF file: {e}")
        return None
    
    # Extract all shapes
    shapes_data = {
        'shapes': extract_all_shapes(graph)
    }
    
    print(f"Extracted {len(shapes_data['shapes'])} shapes")
    
    # Write to file if specified
    if output_filepath:
        try:
            with open(output_filepath, 'w') as f:
                json.dump(shapes_data, f, indent=2)
            print(f"Shapes exported to {output_filepath}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    
    return shapes_data


# Usage example
if __name__ == "__main__":
    # Replace with your SHACL file path
    result = parse_shacl_to_json("shapes.ttl", "shapes.json")
    
    # Or just print as JSON
    if result:
        print("\n" + "="*50)
        print("EXTRACTED SHAPES (JSON):")
        print("="*50)
        print(json.dumps(result, indent=2))
