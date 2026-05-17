# SHACL Shapes Editor — Backend-Frontend Contract

## Overview

This document defines the data format and API contract between the backend (Turtle parsing/serialization) and frontend (tree visualization/editing). Both sides must implement this exactly as specified to ensure seamless integration.

---

## Part 1: Internal Data Format (JSON)

All data exchanged between backend and frontend uses this JSON structure. Every node in the tree, regardless of type, follows the same schema.

### Node Schema

Every node has exactly these four fields:

```typescript
{
  id: string;              // Stable unique identifier (backend generates on parse)
  type: string;            // One of: "NodeShape" | "PropertyShape" | "Constraint" | "LogicalOperator"
  label: string;           // Human-readable display text (shown in the tree UI)
  properties: object;      // SHACL predicates and their RDF values (key-value pairs)
  children: Node[];        // Child nodes (always present, empty array [] for leaves)
}
```

### Node Type Definitions

| Type | SHACL Concept | Example |
|------|---|---|
| `"NodeShape"` | A `sh:NodeShape` with a target declaration | `sh:targetClass ex:Person` |
| `"PropertyShape"` | A `sh:PropertyShape` with `sh:path` | A constraint on a specific property like `ex:age` |
| `"Constraint"` | A leaf constraint predicate | `sh:minCount 1`, `sh:datatype xsd:string` |
| `"LogicalOperator"` | Logical operators that create branches | `sh:or`, `sh:and`, `sh:not`, `sh:xone` |

### Complete Example Tree

```json
{
  "id": "shape-1",
  "type": "NodeShape",
  "label": "PersonShape",
  "properties": {
    "sh:targetClass": "ex:Person"
  },
  "children": [
    {
      "id": "prop-1",
      "type": "PropertyShape",
      "label": "age property",
      "properties": {
        "sh:path": "ex:age"
      },
      "children": [
        {
          "id": "constraint-1",
          "type": "Constraint",
          "label": "minCount = 1",
          "properties": {
            "sh:minCount": 1
          },
          "children": []
        },
        {
          "id": "constraint-2",
          "type": "Constraint",
          "label": "datatype = integer",
          "properties": {
            "sh:datatype": "xsd:integer"
          },
          "children": []
        }
      ]
    },
    {
      "id": "logical-1",
      "type": "LogicalOperator",
      "label": "sh:or",
      "properties": {
        "sh:or": true
      },
      "children": [
        {
          "id": "branch-1",
          "type": "PropertyShape",
          "label": "name (English)",
          "properties": {
            "sh:path": "ex:name",
            "sh:languageIn": ["en"]
          },
          "children": []
        },
        {
          "id": "branch-2",
          "type": "PropertyShape",
          "label": "name (German)",
          "properties": {
            "sh:path": "ex:name",
            "sh:languageIn": ["de"]
          },
          "children": []
        }
      ]
    }
  ]
}
```

### Field Details

**`id`** (string, required)
- Stable unique identifier per node
- Backend generates this during Turtle parsing
- Frontend never modifies this
- Used to reference nodes during editing operations
- Format: any string that's unique within the tree (e.g., `"shape-1"`, `"prop-1"`, `"constraint-1"`)

**`type`** (string, required)
- Determines how both frontend and backend interpret the node
- Must be one of: `"NodeShape"`, `"PropertyShape"`, `"Constraint"`, `"LogicalOperator"`
- Controls validation rules (e.g., a Constraint cannot contain PropertyShape children)

**`label`** (string, required)
- Human-readable text displayed in the frontend tree UI
- Examples:
  - For NodeShape: `"PersonShape"` or the local name of the target class
  - For PropertyShape: `"age property"` or derived from `sh:path`
  - For Constraint: `"minCount = 1"` or `"datatype = xsd:string"`
  - For LogicalOperator: `"sh:or"` or `"sh:and"`
- Can be freely edited by the user in the frontend
- Backend should regenerate intelligently after serialization (or preserve user edits if stored)

**`properties`** (object, required)
- Key-value pairs of SHACL predicates and their RDF values
- Keys are SHACL predicate names: `"sh:minCount"`, `"sh:path"`, `"sh:datatype"`, etc.
- Values are the RDF values (strings, numbers, arrays, or IRIs as needed)
- Examples:
  ```json
  { "sh:minCount": 1 }
  { "sh:datatype": "xsd:string" }
  { "sh:path": "ex:age" }
  { "sh:languageIn": ["en", "de", "fr"] }
  { "sh:targetClass": "ex:Person" }
  ```
- Empty object `{}` is valid for nodes that have no constraints yet

**`children`** (array, required)
- Array of child nodes (recursive)
- Always present, never `null` or `undefined`
- Empty array `[]` for leaf nodes
- Maintains the hierarchical tree structure

---

## Part 2: REST API Contract

The frontend and backend communicate over HTTP using these endpoints.

### Endpoint 1: Parse Turtle to Tree

**Request**
```
POST /api/parse
Content-Type: application/json

{
  "turtle": "... raw Turtle string ..."
}
```

**Response (200 OK)**
```json
{
  "tree": {
    "id": "shape-1",
    "type": "NodeShape",
    "label": "PersonShape",
    "properties": { "sh:targetClass": "ex:Person" },
    "children": [...]
  }
}
```

**Response (400 Bad Request)**
```json
{
  "error": "Invalid Turtle syntax",
  "details": "Line 5: unexpected token"
}
```

**Backend Responsibility:**
- Parse the Turtle string into RDF triples
- Identify NodeShapes, PropertyShapes, Constraints, and LogicalOperators
- Assign unique IDs to every node
- Generate human-readable labels
- Return a fully hydrated tree in the agreed JSON format

---

### Endpoint 2: Serialize Tree to Turtle

**Request**
```
POST /api/serialize
Content-Type: application/json

{
  "tree": {
    "id": "shape-1",
    "type": "NodeShape",
    "label": "PersonShape",
    "properties": { "sh:targetClass": "ex:Person" },
    "children": [...]
  }
}
```

**Response (200 OK)**
```json
{
  "turtle": "... valid Turtle string ..."
}
```

**Response (400 Bad Request)**
```json
{
  "error": "Invalid tree structure",
  "details": "Node shape-1 has invalid children types"
}
```

**Backend Responsibility:**
- Accept the modified tree from the frontend
- Validate the tree structure (catch invalid edits)
- Convert the tree back into valid Turtle syntax
- Return the Turtle string ready for download or further validation

---

### Endpoint 3: Validate Turtle (Optional but Recommended)

**Request**
```
POST /api/validate
Content-Type: application/json

{
  "turtle": "... raw Turtle string ..."
}
```

**Response (200 OK — Valid)**
```json
{
  "valid": true,
  "errors": []
}
```

**Response (200 OK — Invalid)**
```json
{
  "valid": false,
  "errors": [
    "PersonShape targets ex:Person but ex:Person is not defined",
    "PropertyShape prop-1 has sh:path but no constraints"
  ]
}
```

**Backend Responsibility:**
- Run PySHACL validation on the Turtle string
- Return a boolean and a list of human-readable error messages
- Allows frontend to warn the user before export if the shapes graph is invalid

---

## Part 3: Data Invariants (Rules Both Sides Enforce)

These rules ensure the tree always represents valid SHACL.

### Structure Rules

1. **Every node must have an `id`** — unique within the tree, never changed after creation
2. **Every node must have a `type`** — one of the four defined types
3. **`children` must always be an array** — never `null`, never missing
4. **A NodeShape can contain PropertyShapes, LogicalOperators, or Constraints as children**
5. **A PropertyShape can contain Constraints or LogicalOperators as children, not other PropertyShapes**
6. **A Constraint cannot have children** (always `children: []`)
7. **A LogicalOperator can contain PropertyShapes or Constraints as children** (represents branches in `sh:or`, `sh:and`, etc.)

### Edit Rules (Frontend Enforces)

- User cannot delete a NodeShape (root can only be replaced via new parse)
- User cannot move a PropertyShape outside its parent NodeShape
- User cannot move a Constraint to be a direct child of a NodeShape
- Dragging a Constraint to a different PropertyShape is allowed (valid SHACL)

### Serialization Rules (Backend Enforces)

- Backend rejects trees that violate the structure rules
- Backend returns a 400 error with details if the tree is unparseable
- Backend never modifies user-edited `label` values (preserve UX intent)

---

## Part 4: Implementation Checklist

### Backend Must Implement

- [ ] `POST /api/parse` — parse Turtle, return JSON tree
- [ ] `POST /api/serialize` — accept JSON tree, return valid Turtle
- [ ] `POST /api/validate` — validate Turtle with PySHACL
- [ ] Unique ID generation for parsed nodes (UUID or counter-based)
- [ ] Label generation (derive from IRIs or `rdfs:label` if available)
- [ ] Structure validation (reject invalid trees with 400 errors)

### Frontend Must Implement

- [ ] Parse JSON response from `/api/parse` and render as interactive tree
- [ ] Edit node `label` field via inline form
- [ ] Add/delete nodes while respecting structure rules
- [ ] Drag-and-drop to reorder or move nodes (within constraints)
- [ ] POST to `/api/serialize` on export
- [ ] Display export Turtle to user (download or copy)
- [ ] Optionally POST to `/api/validate` and show warnings

---

## Part 5: Example Workflow

1. **User uploads Turtle file**
   - Frontend reads file as text
   - POST to `/api/parse` with raw Turtle
   - Backend parses and returns tree JSON
   - Frontend renders the tree

2. **User edits a node label**
   - Frontend updates local tree (immutably)
   - Changes are reflected in UI immediately

3. **User adds a constraint**
   - Frontend creates a new node with a temporary ID
   - Inserts it into the tree under the selected PropertyShape
   - (ID may be reassigned by backend if re-parsing)

4. **User exports the edited tree**
   - Frontend POST to `/api/serialize` with the modified tree
   - Backend converts back to valid Turtle
   - Frontend allows user to download the `.ttl` file

5. **User validates the result** (optional)
   - Frontend POST to `/api/validate` with the Turtle
   - Backend runs PySHACL
   - If errors, frontend displays them; user can edit and re-export

---

## Questions & Edge Cases

**Q: What if the user creates a node with a new id that the backend hasn't seen?**
A: Frontend can generate temporary IDs (e.g., `"temp-1"`, `"temp-2"`). When serialized, backend can either:
- Accept and preserve them, or
- Regenerate IDs and return the updated tree so frontend stays in sync

**Q: How do we handle nested `sh:or` / `sh:and`?**
A: Each LogicalOperator is a node. Its children are the alternative branches (PropertyShapes or more LogicalOperators). The recursive tree naturally supports arbitrary nesting depth.

**Q: Can a PropertyShape have multiple `sh:path` values?**
A: No — SHACL spec says `sh:path` is a single predicate. If you need to match multiple paths, use multiple PropertyShapes as siblings.

**Q: Who owns the `label` field if the backend regenerates it?**
A: Frontend owns it while editing. Backend should preserve user edits. If re-parsing from scratch, backend generates fresh labels. This is a nice-to-have; frontend can also regenerate intelligently.

---

## Sign-Off

Both team members agree to implement the frontend and backend strictly according to this contract.

**Frontend Developer (you):** Implement tree UI, editing, and API calls as specified.

**Backend Developer (partner):** Implement parsing, serialization, and validation; return JSON in the exact format above.

Once both sides are ready, integration should require zero data format changes — only connecting the endpoints.

---

**Document Version:** 1.0  
**Date:** May 12, 2026  
**Status:** Agreed and finalized
