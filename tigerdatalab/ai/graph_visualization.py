"""Developer utilities for inspecting graph definitions without executing them."""
from __future__ import annotations

from .async_graph import AsyncGraph
from .graph import Graph


def to_mermaid(graph: Graph | AsyncGraph) -> str:
    """Render a graph definition as Mermaid flowchart source.

    Callable conditions are shown as labeled conditional edges where labels
    exist; this function never executes graph actions or condition callbacks.
    """
    graph.validate()
    lines = ["flowchart TD"]
    for name, node in graph.nodes.items():
        safe_name = "n_" + "".join(ch if ch.isalnum() else "_" for ch in name)
        label = name.replace('"', "'")
        lines.append(f'    {safe_name}["{label}"]')
    for edge in graph.edges:
        source = "n_" + "".join(ch if ch.isalnum() else "_" for ch in edge.source)
        target = "n_" + "".join(ch if ch.isalnum() else "_" for ch in edge.target)
        label = edge.label or ("conditional" if edge.condition is not None else "")
        if label:
            label = label.replace('"', "'").replace("|", "/")
            lines.append(f'    {source} -->|"{label}"| {target}')
        else:
            lines.append(f"    {source} --> {target}")
    return "\n".join(lines)
