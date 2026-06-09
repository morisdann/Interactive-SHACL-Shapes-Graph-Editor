from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph
from backend.shacl_parser import parse_shacl, parse_json
import tempfile
import os

app = Flask(__name__)
CORS(app, origins="*")

@app.route("/api/parse", methods=["POST"])
def parse():
    body = request.get_json()
    turtle = body["turtle"]

    g = Graph()
    g.parse(data=turtle, format="turtle")

    return jsonify(parse_shacl(g))


@app.route("/api/serialize", methods=["POST"])
def serialize():
    body = request.get_json()
    tree = body["tree"]

    f = tempfile.NamedTemporaryFile(suffix=".ttl", delete=False)
    path = f.name
    f.close()

    parse_json(tree, path)

    turtle = open(path, "r", encoding="utf-8").read()
    os.unlink(path)

    return jsonify({"turtle": turtle})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
