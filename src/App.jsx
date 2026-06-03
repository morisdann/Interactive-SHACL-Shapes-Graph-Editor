import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, Handle, Position } from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import dagre from "@dagrejs/dagre"
import { useState, useCallback, useEffect } from "react"

const initialData = {
  id: "shape-1",
  type: "NodeShape",
  label: "PersonShape",
  properties: {
    "sh:targetClass": "ex:Person"
  },
  children: [
    {
      id: "prop-1",
      type: "PropertyShape",
      label: "age property",
      properties: { "sh:path": "ex:age" },
      children: [
        {
          id: "constraint-1",
          type: "Constraint",
          label: "minCount = 1",
          properties: { "sh:minCount": 1 },
          children: []
        },
        {
          id: "constraint-2",
          type: "Constraint",
          label: "datatype = integer",
          properties: { "sh:datatype": "xsd:integer" },
          children: []
        }
      ]
    },
    {
      id: "prop-2",
      type: "PropertyShape",
      label: "name property",
      properties: { "sh:path": "ex:name" },
      children: [
        {
          id: "constraint-3",
          type: "Constraint",
          label: "minLength = 2",
          properties: { "sh:minLength": 2 },
          children: []
        },
        {
          id: "constraint-4",
          type: "Constraint",
          label: "maxLength = 100",
          properties: { "sh:maxLength": 100 },
          children: []
        }
      ]
    },
    {
      id: "prop-3",
      type: "PropertyShape",
      label: "email property",
      properties: { "sh:path": "ex:email" },
      children: [
      {
  id: "constraint-5",
  type: "Constraint",
  label: "pattern = ^[^@]+@[^@]+$",
  properties: { "sh:pattern": "^[^@]+@[^@]+$" },
  children: []
}
      ]
    },
    {
      id: "logical-1",
      type: "LogicalOperator",
      label: "sh:or",
      properties: { "sh:or": true },
      children: [
        {
          id: "branch-1",
          type: "PropertyShape",
          label: "name (English)",
          properties: { "sh:path": "ex:name", "sh:languageIn": ["en"] },
          children: [
            {
              id: "constraint-6",
              type: "Constraint",
              label: "minCount = 1",
              properties: { "sh:minCount": 1 },
              children: []
            }
          ]
        },
        {
          id: "branch-2",
          type: "PropertyShape",
          label: "name (German)",
          properties: { "sh:path": "ex:name", "sh:languageIn": ["de"] },
          children: [
            {
              id: "constraint-7",
              type: "Constraint",
              label: "minCount = 1",
              properties: { "sh:minCount": 1 },
              children: []
            }
          ]
        }
      ]
    }
  ]
}
function findNodeById(node, id) {

  if (node.id === id) return node

  if (!node.children) return null
   for (const child of node.children) {
     const found = findNodeById(child, id)
     if (found) return found
  }
  return null
}
function updateNodeInTree(node, targetId, updatedFields) {
  if (node.id === targetId) {
    return { ...node, ...updatedFields }
  }
  if (!node.children) return node      
  return {
    ...node,
    children: node.children.map(child =>
      updateNodeInTree(child, targetId, updatedFields)
    )
  }
}

function deleteNode(node,nodeId){

  if (!node.children) return node  

  for (const child of node.children){
if(child.id === nodeId){
  return {
      ...node,
       children: node.children.filter(n => n.id !== nodeId)
    }
}
  }
  return {
    ...node,
    children: node.children.map(child =>
      deleteNode(child, nodeId)
    )
  }


}

function treeToFlow(node, nodes = [], edges = []) {
  nodes.push({
          id: node.id,
       position: { x: 0, y: 0 },
       data: { label: node.label, type: node.type, properties: node.properties },
  })
  if (node.children) {
    node.children.forEach(child => {
          edges.push({ id: `e-${node.id}-${child.id}`, source: node.id, target: child.id, type: "smoothstep" })
      treeToFlow(child, nodes, edges)
    })
  }
  return { nodes, edges }
}

const NODE_WIDTH = 180
const NODE_HEIGHT = 50

function getLayoutedElements(nodes, edges) {

  const g = new dagre.graphlib.Graph()

     g.setGraph({ rankdir: "TB", ranksep: 80, nodesep: 60 })
    g.setDefaultEdgeLabel(() => ({}))
        nodes.forEach(node => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
      edges.forEach(edge => g.setEdge(edge.source, edge.target))
         dagre.layout(g)
  
         return {
    nodes: nodes.map(node => {
       const { x, y } = g.node(node.id)
        return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
    }),
    edges
  }
}

function convertTreeToFlow(treeData) {
  const { nodes, edges } = treeToFlow(treeData)
  return getLayoutedElements(nodes, edges)
}

const typeStyles = {
  NodeShape:       { bg: "#e8f4fd", border: "#3a8fd1" },
  PropertyShape:   { bg: "#edf7ee", border: "#3aaa5c" },
  Constraint:      { bg: "#fdf6e8", border: "#e6a817" },
  LogicalOperator: { bg: "#f5edfb", border: "#9b5cc4" },
}

function ShapeNode({ data, selected }) {
  const style = typeStyles[data.type] || { bg: "#f5f5f5", border: "#aaa" }
  
  const [isEditing, setEditing] = useState(false)
  const propertyKey = Object.keys(data.properties).find(k => k !== "rdf:about") || Object.keys(data.properties)[0]

  const [editValue, setEditValue] = useState("")

  return (
    <div
      onDoubleClick={(e) => {
  e.stopPropagation()
  const currentValue = String(Object.values(data.properties)[0])
  setEditValue(currentValue)
  setEditing(true)

}}
      style={{
        background: selected ? "#eef0ff" : style.bg,
        border: `2px solid ${selected ? "#5b6af5" : style.border}`,
        borderRadius: "8px", padding: "8px 14px",
        minWidth: "160px", textAlign: "center",
        fontFamily: "'Segoe UI', Arial, sans-serif", fontSize: "13px",

      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: style.border }} />

      <div style={{ fontSize: "10px", color: style.border, fontWeight: 700, textTransform: "uppercase", marginBottom: "3px" }}>
        {data.type}
      </div>

      {isEditing ? (
        <input
          type="text"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          autoFocus
          onKeyDown={(e) => { if (e.key === "Enter") {  if (editValue.trim() !== "") data.onSave(propertyKey, editValue)
             setEditing(false) }}
            }
          onBlur={() =>  { if (editValue.trim() !== "") data.onSave(propertyKey, editValue)
            setEditing(false)}
          }
          style={{
            width: "100%", padding: "4px 6px",
            border: "1.5px solid #cdd", borderRadius: "4px",
            fontSize: "13px", boxSizing: "border-box",
          }}
        />
      ) : (
        <div style={{ fontWeight: 600, color: "#1a1a2e" }}>{data.label}</div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: style.border }} />
    </div>
  )
}

const nodeTypes = { shapeNode: ShapeNode }


function addChildToNode(node, parentId, newChild) {
  if (node.id === parentId) {
    return {
      ...node,
      children: [...node.children, newChild] 
    }
  }

  if (!node.children || node.children.length === 0) {
    return node  
  }

  return {
    ...node,
    children: node.children.map(child =>
      addChildToNode(child, parentId, newChild) 
    )
  }
}

function findParentNode(node, targetId) {
 
  if (!node.children) return null
        for (const child of node.children){

if(child.id == targetId) { 

return node
        }
      }
let  parent  = null
        for(const child of node.children){

          parent = findParentNode(child,targetId)
            
          if(parent !== null){
            return parent
          }

        }

        return null
        }

function NodeDetail({ node, onSave, onAddChild, onDelete, onCopy, onPaste, clipboard }) {
  const [newConstraintType, setNewConstraintType] = useState("sh:minCount")

  return (
    <div style={{
      background: "#fff",
      border: "1.5px solid #d0d5e8",
      borderRadius: "10px",
      padding: "20px",
      fontFamily: "'Segoe UI', Arial, sans-serif",
    }}>
      <h3 style={{ margin: "0 0 6px", fontSize: "13px", color: "#888", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Selected Node
      </h3>
      <p style={{ margin: "0 0 12px", fontSize: "16px", fontWeight: 600, color: "#1a1a2e" }}>
        {node.type}
      </p>

      <div style={{ marginBottom: "16px" }}>
        {Object.entries(node.properties).map(([key, value]) => (
          <div key={key} style={{ fontSize: "13px", color: "#444", marginBottom: "4px" }}>
            <span style={{ color: "#888" }}>{key}: </span>
            <span style={{ fontWeight: 600 }}>{String(value)}</span>
          </div>
        ))}
      </div>

      {(node.type === "PropertyShape" || node.type === "LogicalOperator") && (
        <div style={{ marginBottom: "10px" }}>
          <label style={{ display: "block", fontSize: "12px", color: "#666", marginBottom: "4px" }}>
            Constraint type to add
          </label>
          <select
            value={newConstraintType}
            onChange={e => setNewConstraintType(e.target.value)}
            style={{
              width: "100%", padding: "6px 10px",
              borderRadius: "6px", border: "1.5px solid #cdd",
              fontSize: "13px", marginBottom: "8px",
              boxSizing: "border-box",
            }}
          >
            {[
              "sh:minCount", "sh:maxCount", "sh:datatype", "sh:nodeKind",
              "sh:class", "sh:minInclusive", "sh:maxInclusive",
              "sh:minExclusive", "sh:maxExclusive", "sh:minLength",
              "sh:maxLength", "sh:pattern", "sh:languageIn"
            ].map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      )}

      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
        {(node.type === "PropertyShape" || node.type === "LogicalOperator") && (
          <button
            onClick={() => onAddChild(node.id, newConstraintType)}
            style={{
              padding: "7px 16px", background: "#02e139",
              color: "#fff", border: "none", borderRadius: "6px",
              cursor: "pointer", fontSize: "13px", fontWeight: 600,
            }}
          >
            Add Node
          </button>
        )}

        {(node.type === "PropertyShape" || node.type === "Constraint") && (
          <button
            onClick={() => onCopy()}
            style={{
              padding: "7px 16px", background: "#10196c",
              color: "#fff", border: "none", borderRadius: "6px",
              cursor: "pointer", fontSize: "13px", fontWeight: 600,
            }}
          >
            Copy
          </button>
        )}

        {(node.type === "PropertyShape" && clipboard !== null) && (
          <button
            onClick={() => onPaste()}
            style={{
              padding: "7px 16px", background: "#5be1f5",
              color: "#fff", border: "none", borderRadius: "6px",
              cursor: "pointer", fontSize: "13px", fontWeight: 600,
            }}
          >
            Paste
          </button>
        )}

        <button
          onClick={() => onDelete(node.id)}
          style={{
            padding: "7px 16px", background: "#d00505c8",
            color: "#fff", border: "none", borderRadius: "6px",
            cursor: "pointer", fontSize: "13px", fontWeight: 600,
          }}
        >
          Delete Node
        </button>
      </div>
    </div>
  )
}

function ImportData({ onSave }) {

  const [turtleInput, setTurtleInput] = useState("")

  function handleFileUpload(e) {
  const file = e.target.files[0]      
  if (!file) return                     

  const reader = new FileReader()

  reader.onload = (event) => {
    setTurtleInput(event.target.result)
  }

  reader.readAsText(file)              
}

  return (
    <div style={{
      background: "#fff",
      border: "1.5px solid #d0d5e8",
      borderRadius: "10px",
      padding: "20px",
      fontFamily: "'Segoe UI', Arial, sans-serif",
    }}>
      <h3 style={{ margin: "0 0 6px", fontSize: "13px", color: "#888", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        Import Data
      </h3>

      <label style={{ display: "block", fontSize: "12px", color: "#666", marginBottom: "4px" }}>
        Paste Turtle / SHACL here
      </label>

      <textarea
        value={turtleInput}
        onChange={(e) => setTurtleInput(e.target.value)}
        rows={3}
        style={{
          display: "block",
          width: "100%",
          padding: "7px 10px",
          border: "1.5px solid #cdd",
          borderRadius: "6px",
          fontSize: "13px",
          fontFamily: "monospace",
          boxSizing: "border-box",
          marginBottom: "14px",
          resize: "vertical",
        }}
      />

    <label style={{ display: "block", fontSize: "12px", color: "#666", marginBottom: "8px" }}>
    Or upload a .ttl file
    </label>
    <input
    type="file"
    accept=".ttl"
    onChange={handleFileUpload}
    style={{ marginBottom: "14px", fontSize: "13px" }}
    />
      <div style={{ display: "flex", gap: "8px" }}>
        <button
          onClick={() => onSave(turtleInput)}
          style={{
            padding: "7px 16px",
            background: "#5b6af5",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "13px",
            fontWeight: 600,
          }}
        >
          Confirm
        </button>
      </div>

    </div>
  )
}
function App() {
  const [treeData, setTreeData] = useState(initialData)

  const [selectedNodeId, setSelectedNodeId] = useState(null)
  const [clipboard, setClipboard] = useState(null)
   const [allTrees, setAllTrees] = useState([])

  const { nodes: layoutedNodes, edges: layoutedEdges } = convertTreeToFlow(treeData)
const flowNodes = layoutedNodes.map(n => ({ ...n, type: "shapeNode", selected: n.id === selectedNodeId, key: n.id, data: {
    ...n.data,
    onSave: (propertyKey, newValue) => {
  if (n.data.type === "LogicalOperator") {
    handleSave(n.id, { label: newValue, properties: { [newValue]: true } })
  } else {
    handleSave(n.id, {
      label: `${propertyKey.split(":")[1]} = ${newValue}`,
      properties: { [propertyKey]: newValue }
    })
  }
}
  } }))
const [nodes, setNodes, onNodesChange] = useNodesState([])
const [edges, setEdges, onEdgesChange] = useEdgesState([])
useEffect(() => {
  setNodes(flowNodes)
  setEdges(layoutedEdges)
}, [treeData, selectedNodeId])



const onNodeClick = useCallback((event, node) => {
  setSelectedNodeId(node.id)
}, [])


  const selectedNode = selectedNodeId
    ? findNodeById(treeData, selectedNodeId)
    : null

  
  function handleSave(nodeId, updatedFields) {
    setTreeData(prev => updateNodeInTree(prev, nodeId, updatedFields))
  }

const constraintDefaults = {
  "sh:minCount":      { value: 1,              label: "minCount = 1" },
  "sh:maxCount":      { value: 1,              label: "maxCount = 1" },
  "sh:datatype":      { value: "xsd:string",   label: "datatype = xsd:string" },
  "sh:nodeKind":      { value: "sh:IRI",       label: "nodeKind = sh:IRI" },
  "sh:class":         { value: "ex:Class",     label: "class = ex:Class" },
  "sh:minInclusive":  { value: 0,              label: "minInclusive = 0" },
  "sh:maxInclusive":  { value: 100,            label: "maxInclusive = 100" },
  "sh:minExclusive":  { value: 0,              label: "minExclusive = 0" },
  "sh:maxExclusive":  { value: 100,            label: "maxExclusive = 100" },
  "sh:minLength":     { value: 1,              label: "minLength = 1" },
  "sh:maxLength":     { value: 100,            label: "maxLength = 100" },
  "sh:pattern":       { value: ".*",           label: "pattern = .*" },
  "sh:languageIn":    { value: "en",           label: "languageIn = en" },
}

function handleNewChild(nodeId, constraintType) {
  const defaults = constraintDefaults[constraintType]
  const newChild = {
    id: crypto.randomUUID(),
    type: "Constraint",
    label: defaults.label,
    properties: { [constraintType]: defaults.value },
    children: []
  }
  setTreeData(prev => addChildToNode(prev, nodeId, newChild))
}


function handleDelete(nodeId) { setTreeData(prev => deleteNode(prev, nodeId))}


function handleDrop(draggedId, targetId) {
  
  if (draggedId === targetId) return

  const draggedNode = findNodeById(treeData,draggedId)
  const targetNode = findNodeById(treeData,targetId)
  const draggedParent = findParentNode(treeData,draggedId)
  const targetParent = findParentNode(treeData,targetId)
  

  if (draggedParent && targetParent && targetParent.id === draggedParent.id) {

    // reorder
        
  const filtered = draggedParent.children.filter(c => c.id !== draggedId)
  const targetIndex = filtered.findIndex(c => c.id === targetId)
  const newChildren = [...filtered]
  newChildren.splice(targetIndex, 0, draggedNode)
  setTreeData(prev => updateNodeInTree(prev, draggedParent.id, { children: newChildren }))

    
  } 
  
  else if (draggedNode.type === "Constraint" && targetNode.type === "PropertyShape" ) {

    // move 

     
    setTreeData(addChildToNode(deleteNode(treeData,draggedId),targetId,draggedNode))
   

  } 
}

  async function handleImport(turtleText) {
   const response = await fetch("/api/parse", {
    method: "POST",

      headers: { "Content-Type": "application/json" },


    body: JSON.stringify({ turtle: turtleText })
  })
  const data = await response.json()
  if (data.trees) {
    setAllTrees(data.trees)
     setTreeData(data.trees[0])
  } else {
     setAllTrees([data.tree])
      setTreeData(data.tree)
  }
}

async function handleExport() {

  const response = await fetch("/api/serialize", {
     method: "POST",

    headers: { "Content-Type": "application/json" },

    body: JSON.stringify({ tree: treeData })
   } )
  const data = await response.json()

   const blob = new Blob([data.turtle], { type: "text/turtle" })

   const url = URL.createObjectURL(blob)

   const a = document.createElement("a")

   a.href = url

   a.download = "shapes.ttl"


   a.click()
   URL.revokeObjectURL(url)
}


function onNodeDragStop(event, draggedNode) {
  const { nodes: currentNodes } = convertTreeToFlow(treeData)

  const target = currentNodes.find(n => {
    if (n.id === draggedNode.id) return false
    const dx = Math.abs(n.position.x - draggedNode.position.x)
    const dy = Math.abs(n.position.y - draggedNode.position.y)
    return dx < NODE_WIDTH && dy < NODE_HEIGHT
  })

  if (target) {
    handleDrop(draggedNode.id, target.id)
  }
}


function handleCopy() {
  if (selectedNode.type === "Constraint") {
    setClipboard([{ ...selectedNode }])
  } else {
    setClipboard(selectedNode.children
      .filter(n => n.type === "Constraint")
      .map(child => ({ ...child })))
  }
}


function handlePaste() {
  if (!clipboard) return
  let updatedTree = treeData
  clipboard.forEach(constraint => {
    updatedTree = addChildToNode(updatedTree, selectedNode.id, {
      ...constraint,
      id: crypto.randomUUID()
    })
  })
  setTreeData(updatedTree)
}



  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "1fr 320px",
      gridTemplateRows: "auto 1fr",
      gap: "20px",
      padding: "24px",
      height: "100vh",
      background: "#f7f8fc",
      fontFamily: "'Segoe UI', Arial, sans-serif",
      boxSizing: "border-box",
    }}>

     {/* Header full width */}
<div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
  <div>
    <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#1a1a2e" }}>
      SHACL Shapes Graph Editor
    </h1>
    <p style={{ margin: "2px 0 0", fontSize: "12px", color: "#888" }}>
      Double-click a node to edit · Drag to move or reorder · Right panel for actions
    </p>
    { allTrees.length > 1 && (
  <select
    onChange={e => {
      setTreeData(allTrees[Number(e.target.value)])
      setSelectedNodeId(null)
    } } 
    style={{
      marginTop: "6px",
      padding: "5px 10px",
      borderRadius: "6px",
      border: "1.5px solid #cdd",
      fontSize: "13px",
      cursor: "pointer",
    } }
  >
    {allTrees.map((t, i) => (
      <option key={i} value={i}>{t.label}</option>
    ) ) }
  </select>
)}

  </div>
  <button onClick={handleExport} style={{ padding: "8px 18px", background: "#1a1a2e", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "13px", fontWeight: 600 }}>
    Export Turtle
  </button>
</div>

{/* Tree panel — spans full height of second row */}
<div style={{ background: "#fff", borderRadius: "10px", border: "1.5px solid #e0e4f0", overflow: "hidden" }}>
  <ReactFlow
    nodes={nodes}
    edges={edges}
    onNodesChange={onNodesChange}
    onEdgesChange={onEdgesChange}
    onNodeClick={onNodeClick}
    nodeTypes={nodeTypes}
    fitView
    fitViewOptions={{ padding: 0.2 }}
    onNodeDragStop={onNodeDragStop}
  >
    <Background color="#e0e4f0" gap={20} />
    <Controls />
    <MiniMap nodeColor={n => typeStyles[n.data?.type]?.border || "#aaa"} />
  </ReactFlow>
</div>

{/* Right panel — import, detail, legend stacked */}
<div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>

  <ImportData onSave={handleImport} />

  {selectedNode ? (
    <NodeDetail
      key={selectedNode.id}
      node={selectedNode}
      onSave={handleSave}
      onAddChild={handleNewChild}
      onDelete={handleDelete}
      onCopy={handleCopy}
      onPaste={handlePaste}
      clipboard={clipboard}
    />
  ) : (
    <div style={{ background: "#fff", border: "1.5px dashed #d0d5e8", borderRadius: "10px", padding: "32px 20px", textAlign: "center", color: "#aaa", fontSize: "14px" }}>
      <div style={{ fontSize: "28px", marginBottom: "8px" }}>←</div>
      Select a node to see its details
    </div>
  )}

  <div style={{ padding: "14px", background: "#fff", borderRadius: "10px", border: "1.5px solid #e0e4f0" }}>
    <p style={{ margin: "0 0 8px", fontSize: "11px", color: "#999", textTransform: "uppercase", letterSpacing: "0.05em" }}>Node types</p>
    {[
      { label: "NodeShape",       color: "#3a8fd1", desc: "Top-level shape targeting a class" },
      { label: "PropertyShape",   color: "#3aaa5c", desc: "Constrains a specific property" },
      { label: "Constraint",      color: "#e6a817", desc: "Individual constraint value" },
      { label: "LogicalOperator", color: "#9b5cc4", desc: "Logical branch (sh:or, sh:and, sh:not)" },
    ].map(({ label, color, desc }) => (
      <div key={label} style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginBottom: "6px" }}>
        <span style={{ width: "10px", height: "10px", borderRadius: "3px", background: color, display: "inline-block", marginTop: "3px", flexShrink: 0 }} />
        <div>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#444" }}>{label}</span>
          <span style={{ fontSize: "11px", color: "#999", marginLeft: "6px" }}>{desc}</span>
        </div>
      </div>
    ))}
  </div>

</div>


    </div>
  )
}

export default App