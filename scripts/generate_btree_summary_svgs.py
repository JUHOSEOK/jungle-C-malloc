#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import html


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str
    kind: str


@dataclass(frozen=True)
class Diagram:
    filename: str
    nodes: List[Node]
    edges: List[Tuple[str, str]]
    links: List[Tuple[str, str]] = field(default_factory=list)


BOX_HEIGHT = 44
H_GAP = 28
V_GAP = 92
MARGIN_X = 28
MARGIN_Y = 28

STYLES: Dict[str, Dict[str, str]] = {
    "root": {"fill": "#1d3557", "stroke": "#1d3557", "text": "#ffffff"},
    "internal": {"fill": "#eef6ff", "stroke": "#457b9d", "text": "#16324f"},
    "leaf": {"fill": "#fff4dd", "stroke": "#e9a400", "text": "#5c3b00"},
    "root_green": {"fill": "#0b6e4f", "stroke": "#0b6e4f", "text": "#ffffff"},
    "leaf_green": {"fill": "#edf7f3", "stroke": "#55a37a", "text": "#123524"},
    "bad": {"fill": "#ffe5e5", "stroke": "#d00000", "text": "#7a0000"},
    "note": {"fill": "#f1f3f5", "stroke": "#adb5bd", "text": "#343a40"},
}


DIAGRAMS = [
    Diagram(
        filename="01-bst.svg",
        nodes=[
            Node("A", "8", "root"),
            Node("B", "3", "internal"),
            Node("C", "12", "internal"),
            Node("D", "1", "leaf"),
            Node("E", "5", "leaf"),
            Node("F", "10", "leaf"),
            Node("G", "15", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "F"), ("C", "G")],
    ),
    Diagram(
        filename="02-btree-concept.svg",
        nodes=[
            Node("R", "20 | 40", "root_green"),
            Node("A", "< 20", "leaf_green"),
            Node("B", "20 ~ 40", "leaf_green"),
            Node("C", "> 40", "leaf_green"),
        ],
        edges=[("R", "A"), ("R", "B"), ("R", "C")],
    ),
    Diagram(
        filename="03-invalid-structure.svg",
        nodes=[
            Node("A", "30", "bad"),
            Node("B", "10", "bad"),
            Node("C", "20", "bad"),
            Node("D", "40", "bad"),
        ],
        edges=[("A", "B"), ("A", "C"), ("A", "D")],
    ),
    Diagram(
        filename="04-step-1.svg",
        nodes=[Node("A", "1 | 15", "root")],
        edges=[],
    ),
    Diagram(
        filename="05-step-2.svg",
        nodes=[
            Node("A", "2", "root"),
            Node("B", "1", "leaf"),
            Node("C", "15", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="06-step-3.svg",
        nodes=[
            Node("A", "2 | 15", "root"),
            Node("B", "1", "leaf"),
            Node("C", "5", "leaf"),
            Node("D", "30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C"), ("A", "D")],
    ),
    Diagram(
        filename="07-step-4.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "2", "internal"),
            Node("C", "30", "internal"),
            Node("D", "1", "leaf"),
            Node("E", "5", "leaf"),
            Node("F", "20", "leaf"),
            Node("G", "90", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "F"), ("C", "G")],
    ),
    Diagram(
        filename="08-step-5.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "2 | 7", "internal"),
            Node("C", "30", "internal"),
            Node("D", "1", "leaf"),
            Node("E", "5", "leaf"),
            Node("F", "9", "leaf"),
            Node("G", "20", "leaf"),
            Node("H", "90", "leaf"),
        ],
        edges=[
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("B", "E"),
            ("B", "F"),
            ("C", "G"),
            ("C", "H"),
        ],
    ),
    Diagram(
        filename="09-step-6.svg",
        nodes=[
            Node("A", "7 | 15", "root"),
            Node("B", "2", "internal"),
            Node("C", "9", "internal"),
            Node("D", "30", "internal"),
            Node("E", "1", "leaf"),
            Node("F", "5", "leaf"),
            Node("G", "8", "leaf"),
            Node("H", "10", "leaf"),
            Node("I", "20", "leaf"),
            Node("J", "90", "leaf"),
        ],
        edges=[
            ("A", "B"),
            ("A", "C"),
            ("A", "D"),
            ("B", "E"),
            ("B", "F"),
            ("C", "G"),
            ("C", "H"),
            ("D", "I"),
            ("D", "J"),
        ],
    ),
    Diagram(
        filename="10-step-7-final.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "7", "internal"),
            Node("C", "50", "internal"),
            Node("D", "2", "internal"),
            Node("E", "9", "internal"),
            Node("F", "30", "internal"),
            Node("G", "70", "internal"),
            Node("H", "1", "leaf"),
            Node("I", "5", "leaf"),
            Node("J", "8", "leaf"),
            Node("K", "10", "leaf"),
            Node("L", "20", "leaf"),
            Node("M", "40", "leaf"),
            Node("N", "60", "leaf"),
            Node("O", "90", "leaf"),
        ],
        edges=[
            ("A", "B"),
            ("A", "C"),
            ("B", "D"),
            ("B", "E"),
            ("C", "F"),
            ("C", "G"),
            ("D", "H"),
            ("D", "I"),
            ("E", "J"),
            ("E", "K"),
            ("F", "L"),
            ("F", "M"),
            ("G", "N"),
            ("G", "O"),
        ],
    ),
    Diagram(
        filename="11-bplustree-structure.svg",
        nodes=[
            Node("A", "15 | 50", "root"),
            Node("B", "8", "internal"),
            Node("C", "30", "internal"),
            Node("D", "70", "internal"),
            Node("E", "1 | 5 | 7", "leaf"),
            Node("F", "8 | 10", "leaf"),
            Node("G", "15 | 20", "leaf"),
            Node("H", "30 | 40", "leaf"),
            Node("I", "50 | 60", "leaf"),
            Node("J", "70 | 90", "leaf"),
        ],
        edges=[
            ("A", "B"),
            ("A", "C"),
            ("A", "D"),
            ("B", "E"),
            ("B", "F"),
            ("C", "G"),
            ("C", "H"),
            ("D", "I"),
            ("D", "J"),
        ],
        links=[("E", "F"), ("F", "G"), ("G", "H"), ("H", "I"), ("I", "J")],
    ),
    Diagram(
        filename="12-bplustree-leaf-chain.svg",
        nodes=[
            Node("A", "Leaf linked list", "note"),
            Node("B", "1 | 5 | 7", "leaf"),
            Node("C", "8 | 10", "leaf"),
            Node("D", "15 | 20", "leaf"),
            Node("E", "30 | 40", "leaf"),
            Node("F", "50 | 60", "leaf"),
            Node("G", "70 | 90", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C"), ("A", "D"), ("A", "E"), ("A", "F"), ("A", "G")],
        links=[("B", "C"), ("C", "D"), ("D", "E"), ("E", "F"), ("F", "G")],
    ),
    Diagram(
        filename="13-bplustree-insert-start.svg",
        nodes=[Node("A", "10 | 20", "root")],
        edges=[],
    ),
    Diagram(
        filename="14-bplustree-insert-root-split.svg",
        nodes=[
            Node("A", "20", "root"),
            Node("B", "10", "leaf"),
            Node("C", "20 | 30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
        links=[("B", "C")],
    ),
    Diagram(
        filename="15-bplustree-insert-second-split.svg",
        nodes=[
            Node("A", "20 | 25", "root"),
            Node("B", "10", "leaf"),
            Node("C", "20", "leaf"),
            Node("D", "25 | 30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C"), ("A", "D")],
        links=[("B", "C"), ("C", "D")],
    ),
    Diagram(
        filename="16-btree-delete-simple-before.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "5 | 10", "leaf"),
            Node("C", "20 | 30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="17-btree-delete-simple-after.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "5", "leaf"),
            Node("C", "20 | 30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="18-btree-redistribute-before.svg",
        nodes=[
            Node("A", "15", "root"),
            Node("B", "5", "leaf"),
            Node("C", "20 | 30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="19-btree-redistribute-after.svg",
        nodes=[
            Node("A", "20", "root"),
            Node("B", "15", "leaf"),
            Node("C", "30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="20-btree-merge-before.svg",
        nodes=[
            Node("A", "20", "root"),
            Node("B", "10", "leaf"),
            Node("C", "30", "leaf"),
        ],
        edges=[("A", "B"), ("A", "C")],
    ),
    Diagram(
        filename="21-btree-merge-after.svg",
        nodes=[Node("A", "20 | 30", "root")],
        edges=[],
    ),
]


def box_width(label: str) -> int:
    return max(52, 24 + len(label) * 11)


def build_children(edges: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    children: Dict[str, List[str]] = {}
    for parent, child in edges:
        children.setdefault(parent, []).append(child)
        children.setdefault(child, [])
    return children


def find_root(nodes: Dict[str, Node], edges: List[Tuple[str, str]]) -> str:
    child_ids = {child for _, child in edges}
    for node_id in nodes:
        if node_id not in child_ids:
            return node_id
    raise ValueError("root not found")


def subtree_width(node_id: str, nodes: Dict[str, Node], children: Dict[str, List[str]], cache: Dict[str, float]) -> float:
    if node_id in cache:
        return cache[node_id]
    child_ids = children.get(node_id, [])
    own = float(box_width(nodes[node_id].label))
    if not child_ids:
        cache[node_id] = own
        return own
    total_children = sum(subtree_width(child_id, nodes, children, cache) for child_id in child_ids)
    total_children += H_GAP * (len(child_ids) - 1)
    cache[node_id] = max(own, total_children)
    return cache[node_id]


def assign_positions(
    node_id: str,
    depth: int,
    left: float,
    nodes: Dict[str, Node],
    children: Dict[str, List[str]],
    widths: Dict[str, float],
    positions: Dict[str, Tuple[float, float]],
) -> None:
    width = widths[node_id]
    center_x = left + width / 2
    y = MARGIN_Y + depth * V_GAP
    positions[node_id] = (center_x, y)

    child_ids = children.get(node_id, [])
    if not child_ids:
        return

    total_children = sum(widths[child_id] for child_id in child_ids) + H_GAP * (len(child_ids) - 1)
    start = left + (width - total_children) / 2
    cursor = start
    for child_id in child_ids:
        assign_positions(child_id, depth + 1, cursor, nodes, children, widths, positions)
        cursor += widths[child_id] + H_GAP


def tree_depth(root_id: str, children: Dict[str, List[str]]) -> int:
    child_ids = children.get(root_id, [])
    if not child_ids:
        return 1
    return 1 + max(tree_depth(child_id, children) for child_id in child_ids)


def svg_for_diagram(diagram: Diagram) -> str:
    nodes = {node.node_id: node for node in diagram.nodes}
    children = build_children(diagram.edges)
    for node_id in nodes:
        children.setdefault(node_id, [])

    root_id = find_root(nodes, diagram.edges)
    widths: Dict[str, float] = {}
    total_width = subtree_width(root_id, nodes, children, widths)
    positions: Dict[str, Tuple[float, float]] = {}
    assign_positions(root_id, 0, MARGIN_X, nodes, children, widths, positions)
    depth = tree_depth(root_id, children)

    canvas_width = int(total_width + MARGIN_X * 2)
    canvas_height = int((depth - 1) * V_GAP + BOX_HEIGHT + MARGIN_Y * 2)

    parts: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" '
            f'height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}">'
        ),
        '<defs>',
        '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        '<polygon points="0 0, 10 3.5, 0 7" fill="#2a6f97"/>',
        '</marker>',
        '</defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]

    for parent_id, child_id in diagram.edges:
        px, py = positions[parent_id]
        cx, cy = positions[child_id]
        parent_w = box_width(nodes[parent_id].label)
        child_w = box_width(nodes[child_id].label)
        x1 = px
        y1 = py + BOX_HEIGHT / 2
        x2 = cx
        y2 = cy - BOX_HEIGHT / 2
        mid_y = (y1 + y2) / 2
        parts.append(
            (
                '<path d="M {x1:.1f} {y1:.1f} L {x1:.1f} {mid_y:.1f} '
                'L {x2:.1f} {mid_y:.1f} L {x2:.1f} {y2:.1f}" '
                'fill="none" stroke="#5b6573" stroke-width="2"/>'
            ).format(x1=x1, y1=y1, mid_y=mid_y, x2=x2, y2=y2)
        )
        _ = parent_w + child_w

    for start_id, end_id in diagram.links:
        sx, sy = positions[start_id]
        ex, ey = positions[end_id]
        start_w = box_width(nodes[start_id].label)
        end_w = box_width(nodes[end_id].label)
        x1 = sx + start_w / 2 + 6
        x2 = ex - end_w / 2 - 10
        y = sy
        parts.append(
            (
                f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{ey:.1f}" '
                'stroke="#2a6f97" stroke-width="3" stroke-dasharray="8 6" '
                'marker-end="url(#arrowhead)"/>'
            )
        )

    for node_id, node in nodes.items():
        cx, cy = positions[node_id]
        width = box_width(node.label)
        x = cx - width / 2
        y = cy - BOX_HEIGHT / 2
        style = STYLES[node.kind]
        parts.append(
            (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{BOX_HEIGHT}" '
                f'rx="10" ry="10" fill="{style["fill"]}" stroke="{style["stroke"]}" '
                'stroke-width="2"/>'
            )
        )
        parts.append(
            (
                f'<text x="{cx:.1f}" y="{cy + 1:.1f}" text-anchor="middle" '
                'dominant-baseline="middle" font-family="Arial, sans-serif" '
                f'font-size="18" font-weight="600" fill="{style["text"]}">'
                f'{html.escape(node.label)}</text>'
            )
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "assets" / "b-tree-summary"
    output_dir.mkdir(parents=True, exist_ok=True)
    for diagram in DIAGRAMS:
        target = output_dir / diagram.filename
        target.write_text(svg_for_diagram(diagram), encoding="utf-8")
        print(target.relative_to(output_dir.parent.parent))


if __name__ == "__main__":
    main()
