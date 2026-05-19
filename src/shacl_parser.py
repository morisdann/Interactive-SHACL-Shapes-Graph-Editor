import json
from pathlib import Path

from rdflib import Graph, RDF
from rdflib.namespace import SH


BASE_DIR = Path(__file__).resolve().parent
output_path = BASE_DIR / "data" / "exampleTest.json"

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


    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open("data/exampleTest.json", "w", encoding="utf-8") as f:
        json.dump(shapes, f, indent=2, ensure_ascii=False) 
    print(f"JSON saved to {output_path}")
    return shapes




