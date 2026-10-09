"""Generate a self-contained, read-only HTML graph run inspector."""
from __future__ import annotations

import html
import json
from typing import Any

from .async_graph import AsyncGraph
from .graph import Graph


def render_graph_debugger(graph: Graph | AsyncGraph, run_id: str | None = None) -> str:
    """Return HTML showing graph topology and checkpoint details.

    The HTML is static and does not execute graph nodes. State may contain
    sensitive application data; callers must authorize access and redact state
    before sharing the generated page.
    """
    graph.validate()
    checkpoint = graph.checkpoint_store.load(run_id) if run_id else None
    nodes = []
    completed = set(checkpoint.completed_nodes) if checkpoint else set()
    current = checkpoint.current_node if checkpoint else None
    for name, node in graph.nodes.items():
        status = "completed" if name in completed else ("current" if name == current else "pending")
        nodes.append({
            "name": name,
            "status": status,
            "description": node.description,
            "approval_required": node.approval_required,
            "retries": node.retries,
            "timeout_seconds": node.timeout_seconds,
        })
    edges = [{
        "source": edge.source,
        "target": edge.target,
        "label": edge.label or ("conditional" if edge.condition else ""),
    } for edge in graph.edges]
    run = None if checkpoint is None else {
        "run_id": run_id,
        "graph_name": checkpoint.graph_name,
        "graph_version": checkpoint.graph_version,
        "status": checkpoint.status,
        "steps": checkpoint.steps,
        "current_node": checkpoint.current_node,
        "completed_nodes": checkpoint.completed_nodes,
        "pending_approval": checkpoint.pending_approval,
        "error": checkpoint.error,
        "state": checkpoint.state,
    }
    data = json.dumps({"graph": graph.name, "version": graph.version, "nodes": nodes, "edges": edges, "run": run},
                      ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    title = html.escape(f"TigerDataLab Graph Debugger — {graph.name}")
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>""" + title + """</title>
<style>
:root{color-scheme:light dark;font:14px/1.5 system-ui,sans-serif}body{margin:0;padding:24px;max-width:1200px;margin-inline:auto}
h1{font-size:1.5rem}.muted{opacity:.7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.card{border:1px solid #8886;border-radius:12px;padding:14px;min-width:0}.node{padding:10px;border:1px solid #8888;border-radius:8px;margin:8px 0}
.node.current{border:2px solid #d97706}.node.completed{border-color:#16a34a}.node.pending{opacity:.8}
pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:440px;overflow:auto}button{padding:8px 12px;cursor:pointer}
input{padding:8px;max-width:100%}.edge{font-size:.9rem;opacity:.85}
</style></head><body>
<h1>TigerDataLab Graph Debugger</h1><p class="muted">Read-only graph/run inspector. It never executes graph actions. Refresh the page after the worker advances.</p>
<div class="grid"><section class="card"><h2>Graph</h2><div id="meta"></div><div id="nodes"></div></section>
<section class="card"><h2>Run checkpoint</h2><div id="run"></div><h3>State snapshot</h3><pre id="state"></pre></section>
<section class="card"><h2>Selected node</h2><p id="selected">Select a node to inspect its metadata.</p><h3>Edges</h3><div id="edges"></div></section></div>
<script type="application/json" id="graph-data">""" + data + """</script>
<script>
const d=JSON.parse(document.getElementById('graph-data').textContent);
const el=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
el('meta').innerHTML='<p><b>'+esc(d.graph)+'</b> · version '+esc(d.version)+'</p><p>'+d.nodes.length+' nodes · '+d.edges.length+' edges</p>';
el('nodes').innerHTML=d.nodes.map(n=>'<div class="node '+esc(n.status)+'"><button data-node="'+esc(n.name)+'">'+esc(n.name)+'</button> <small>'+esc(n.status)+'</small></div>').join('');
el('run').innerHTML=d.run?'<p><b>'+esc(d.run.status)+'</b></p><p>Run: '+esc(d.run.run_id)+'</p><p>Steps: '+esc(d.run.steps)+'</p><p>Current: '+esc(d.run.current_node||'—')+'</p><p>Approval: '+esc(d.run.pending_approval||'—')+'</p><p class="muted">'+esc(d.run.error||'No error recorded')+'</p>':'No checkpoint found for the supplied run ID.';
el('state').textContent=d.run?JSON.stringify(d.run.state,null,2):'';
el('edges').innerHTML=d.edges.map(e=>'<div class="edge">'+esc(e.source)+' → '+esc(e.target)+(e.label?' · '+esc(e.label):'')+'</div>').join('')||'No edges';
el('nodes').addEventListener('click',ev=>{const b=ev.target.closest('button[data-node]');if(!b)return;const n=d.nodes.find(x=>x.name===b.dataset.node);el('selected').innerHTML='<b>'+esc(n.name)+'</b><p>Status: '+esc(n.status)+'</p><p>'+esc(n.description||'No description')+'</p><p>Approval required: '+esc(n.approval_required)+'</p><p>Retries: '+esc(n.retries)+'</p><p>Timeout: '+esc(n.timeout_seconds??'none')+'</p><p>Incoming/outgoing edges are shown in the edges panel.</p>';});
</script></body></html>"""
