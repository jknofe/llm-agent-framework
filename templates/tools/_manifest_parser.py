
def parse_manifest(text: str):
    """Parse the flat, regular manifest.yaml written by init/the agent."""
    project, nodes, cur, in_nodes = "", [], None, False
    for line in text.splitlines():
        if line.startswith("project:"):
            project = line.split(":", 1)[1].strip()
        elif line.startswith("nodes:"):
            in_nodes = True
        elif in_nodes:
            s = line.strip()
            if s.startswith("- id:"):
                cur = {"id": s.split(":", 1)[1].strip()}
                nodes.append(cur)
            elif cur is not None and line.startswith("    ") and ":" in s:
                k, v = s.split(":", 1)
                cur[k.strip()] = v.strip()
    return project, nodes


def parse_yaml_list(value: str) -> list:
    return [
        item.strip().strip("\"").strip("'")
        for item in value.strip().strip("[]").split(",")
        if item.strip().strip("\"")
    ]
