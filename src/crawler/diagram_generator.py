import re
from collections import defaultdict

def sanitize_node(label):
    label = str(label).strip()
    label = re.sub(r'[^\w\-]', '_', label)
    return label if label else "Node"

def outline_to_mermaid(text_outline: str) -> str:
    lines = text_outline.strip().splitlines()
    stack = []
    edges = []
    node_labels = {}
    node_ids = {}

    def generate_node_id(label):
        base = re.sub(r"[^\w]", "_", label.strip())
        base = base if base else "Node"
        new_id = base
        i = 1
        while new_id in node_ids:
            i += 1
            new_id = f"{base}_{i}"
        node_ids[new_id] = label
        return new_id

    for line in lines:
        indent = len(line) - len(line.lstrip())
        label = line.strip("- ").strip()
        if not label:
            continue

        node_id = generate_node_id(label)
        node_labels[node_id] = label

        while stack and stack[-1][0] >= indent:
            stack.pop()

        if stack:
            parent_id = stack[-1][1]
            edges.append(f"{parent_id} --> {node_id}")

        stack.append((indent, node_id))

    mermaid_code = "graph LR\n"
    for node_id, label in node_labels.items():
        mermaid_code += f'{node_id}["{label}"]\n'
    for edge in edges:
        mermaid_code += edge + "\n"

    return mermaid_code  # ✅ FIXED: removed ```mermaid fence

def extract_level1_outlines(text_outline: str) -> dict:
    lines = text_outline.strip().splitlines()
    root_indent = len(lines[0]) - len(lines[0].lstrip())
    sections = defaultdict(list)
    current_key = None

    for line in lines[1:]:
        indent = len(line) - len(line.lstrip())
        label = line.strip("- ").strip()

        if indent == root_indent + 2:
            current_key = label
            sections[current_key].append(f"- {label}")
        elif current_key:
            sections[current_key].append("  " + line.strip())

    return sections
