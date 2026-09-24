from __future__ import annotations

import hashlib
import json
import posixpath
from collections import Counter

from app.project_calls import resolve_project_calls


def build_project_understanding(file_results: list[dict]) -> dict:
    frameworks = _framework_inventory(file_results)
    routes = _route_inventory(file_results)
    authentication_controls = _auth_inventory(file_results)
    import_relationships = _resolve_imports(file_results)
    cross_file_calls = resolve_project_calls(
        file_results, import_relationships
    )
    categories = {item["category"] for item in frameworks}

    if "WEB_API" in categories and "FRONTEND_UI" in categories:
        project_type = "FULL_STACK_PROJECT"
    elif "WEB_API" in categories:
        project_type = "WEB_API_PROJECT"
    elif "FRONTEND_UI" in categories:
        project_type = "FRONTEND_PROJECT"
    else:
        project_type = "UNKNOWN_PROJECT"

    graph = _build_project_graph(
        file_results,
        frameworks,
        routes,
        import_relationships,
        cross_file_calls,
    )
    return {
        "project_type": project_type,
        "frameworks": frameworks,
        "routes": routes,
        "authentication_controls": authentication_controls,
        "import_relationships": import_relationships,
        "cross_file_calls": cross_file_calls,
        "graph": graph,
        "counts": {
            "files": len(file_results),
            "frameworks": len(frameworks),
            "routes": len(routes),
            "authentication_controls": len(authentication_controls),
            "resolved_imports": sum(
                item["status"] == "RESOLVED"
                for item in import_relationships
            ),
            "unresolved_imports": sum(
                item["status"] != "RESOLVED"
                for item in import_relationships
            ),
            "resolved_cross_file_calls": len(cross_file_calls),
        },
        "claims": {
            "cross_file_call_resolution": (
                "PARTIAL_STATIC" if cross_file_calls else "UNRESOLVED"
            ),
            "cross_file_call_languages": sorted(
                {
                    "Python"
                    if call["resolution"] == "STATIC_PYTHON_FROM_IMPORT"
                    else "JavaScript"
                    for call in cross_file_calls
                }
            ),
            "cross_file_data_flow": "UNRESOLVED",
            "frameworks_require_file_evidence": True,
            "authentication_effectiveness_proven": False,
        },
    }


def _framework_inventory(file_results: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for result in file_results:
        path = result["artifact"]["relative_path"]
        for framework in result["application_understanding"]["frameworks"]:
            item = grouped.setdefault(
                framework["name"],
                {
                    "name": framework["name"],
                    "category": framework["category"],
                    "status": "CANDIDATE",
                    "evidence_files": [],
                    "evidence_signals": set(),
                },
            )
            item["evidence_files"].append(path)
            item["evidence_signals"].update(framework["evidence"])
            if framework["status"] == "CORROBORATED":
                item["status"] = "CORROBORATED"

    output = []
    for item in grouped.values():
        item["evidence_files"] = sorted(set(item["evidence_files"]))
        item["evidence_signals"] = sorted(item["evidence_signals"])
        output.append(item)
    return sorted(output, key=lambda item: item["name"])


def _route_inventory(file_results: list[dict]) -> list[dict]:
    routes = []
    for result in file_results:
        path = result["artifact"]["relative_path"]
        for route in result["application_understanding"]["routes"]:
            routes.append({"file": path, **route})
    return sorted(
        routes,
        key=lambda item: (
            item["file"],
            item["start_line"],
            item.get("path") or "",
        ),
    )


def _auth_inventory(file_results: list[dict]) -> list[dict]:
    controls = []
    for result in file_results:
        path = result["artifact"]["relative_path"]
        for control in result["application_understanding"][
            "authentication_controls"
        ]:
            controls.append({"file": path, **control})
    return sorted(
        controls,
        key=lambda item: (item["file"], item["start_line"]),
    )


def _build_project_graph(
    file_results: list[dict],
    frameworks: list[dict],
    routes: list[dict],
    import_relationships: list[dict],
    cross_file_calls: list[dict],
) -> dict:
    nodes = []
    edges = []
    file_ids = {}
    framework_ids = {}

    for result in file_results:
        artifact = result["artifact"]
        node_id = _id("FILE", artifact["relative_path"], artifact["sha256"])
        file_ids[artifact["relative_path"]] = node_id
        nodes.append(
            {
                "id": node_id,
                "type": "FILE",
                "attributes": {
                    "relative_path": artifact["relative_path"],
                    "language": result["language"]["candidate"],
                    "sha256": artifact["sha256"],
                },
            }
        )

    for framework in frameworks:
        node_id = _id("FRAMEWORK", framework["name"])
        framework_ids[framework["name"]] = node_id
        nodes.append({"id": node_id, "type": "FRAMEWORK", "attributes": framework})
        for path in framework["evidence_files"]:
            edges.append(
                _edge(
                    "USES_FRAMEWORK",
                    file_ids[path],
                    node_id,
                    {"resolution": "FILE_EVIDENCE"},
                )
            )

    for route in routes:
        node_id = _id(
            "ROUTE",
            route["file"],
            route["start_line"],
            route.get("path"),
            route["methods"],
        )
        nodes.append({"id": node_id, "type": "ROUTE", "attributes": route})
        edges.append(
            _edge("EXPOSES_ROUTE", file_ids[route["file"]], node_id, {})
        )
        framework_id = framework_ids.get(route["framework"])
        if framework_id:
            edges.append(_edge("PROVIDES_ROUTE", framework_id, node_id, {}))

    for relationship in import_relationships:
        if relationship["status"] != "RESOLVED":
            continue
        edges.append(
            _edge(
                "IMPORTS",
                file_ids[relationship["source_file"]],
                file_ids[relationship["target_file"]],
                {
                    "module": relationship["module"],
                    "resolution": relationship["resolution"],
                    "line": relationship["line"],
                },
            )
        )

    for call in cross_file_calls:
        caller_id = _id("FUNCTION", call["source_file"], call["caller_id"])
        callee_id = _id("FUNCTION", call["target_file"], call["callee_id"])
        nodes.extend(
            (
                {
                    "id": caller_id,
                    "type": "FUNCTION",
                    "attributes": {
                        "file": call["source_file"],
                        "name": call["caller"],
                    },
                },
                {
                    "id": callee_id,
                    "type": "FUNCTION",
                    "attributes": {
                        "file": call["target_file"],
                        "name": call["callee"],
                    },
                },
            )
        )
        edges.extend(
            (
                _edge(
                    "CONTAINS", file_ids[call["source_file"]], caller_id, {}
                ),
                _edge(
                    "CONTAINS", file_ids[call["target_file"]], callee_id, {}
                ),
                _edge(
                    "CALLS",
                    caller_id,
                    callee_id,
                    {
                        "resolution": call["resolution"],
                        "call_line": call["call_line"],
                        "import_line": call["import_line"],
                    },
                ),
            )
        )

    nodes = list({node["id"]: node for node in nodes}.values())
    edges = list({edge["id"]: edge for edge in edges}.values())

    node_counts = Counter(node["type"] for node in nodes)
    edge_counts = Counter(edge["type"] for edge in edges)
    return {
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "nodes_by_type": dict(sorted(node_counts.items())),
            "edges_by_type": dict(sorted(edge_counts.items())),
        },
    }


def _resolve_imports(file_results: list[dict]) -> list[dict]:
    paths = {
        result["artifact"]["relative_path"]
        for result in file_results
    }
    python_modules: dict[str, set[str]] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        module = path[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[: -len(".__init__")]
        parts = module.split(".")
        for index in range(len(parts)):
            python_modules.setdefault(".".join(parts[index:]), set()).add(path)

    relationships = []
    for result in file_results:
        source_file = result["artifact"]["relative_path"]
        language = result["language"]["candidate"]
        for item in result["structure"].get("imports", []):
            module = item.get("module")
            candidates: set[str] = set()
            resolution = "NO_LOCAL_MATCH"

            if module and language == "Python":
                candidates = python_modules.get(module.lstrip("."), set())
                resolution = "UNIQUE_PYTHON_MODULE_SUFFIX"
            elif module and language in {"JavaScript", "JavaScript JSX"}:
                candidates = _javascript_candidates(source_file, module, paths)
                resolution = "EXACT_RELATIVE_PATH"

            status = (
                "RESOLVED"
                if len(candidates) == 1
                else "AMBIGUOUS"
                if len(candidates) > 1
                else "UNRESOLVED"
            )
            relationships.append(
                {
                    "source_file": source_file,
                    "module": module,
                    "target_file": (
                        next(iter(candidates))
                        if len(candidates) == 1
                        else None
                    ),
                    "candidate_files": sorted(candidates),
                    "status": status,
                    "resolution": resolution if candidates else "NO_LOCAL_MATCH",
                    "line": item["start_line"],
                }
            )
    return relationships


def _javascript_candidates(
    source_file: str,
    module: str,
    paths: set[str],
) -> set[str]:
    if not module.startswith("."):
        return set()
    base = posixpath.normpath(
        posixpath.join(posixpath.dirname(source_file), module)
    )
    if base == ".." or base.startswith("../"):
        return set()

    candidates = {base}
    if not posixpath.splitext(base)[1]:
        candidates.update(
            f"{base}{extension}"
            for extension in (".js", ".jsx", ".ts", ".tsx")
        )
        candidates.update(
            f"{base}/index{extension}"
            for extension in (".js", ".jsx", ".ts", ".tsx")
        )
    return candidates & paths


def _edge(edge_type: str, source: str, target: str, evidence: dict) -> dict:
    return {
        "id": _id("EDGE", edge_type, source, target, evidence),
        "type": edge_type,
        "source": source,
        "target": target,
        "evidence": evidence,
    }


def _id(*parts) -> str:
    encoded = json.dumps(
        parts,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "project:" + hashlib.sha256(encoded).hexdigest()[:24]
