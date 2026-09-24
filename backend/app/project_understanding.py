from __future__ import annotations

import hashlib
import json
import posixpath
from collections import Counter

from app.project_calls import resolve_project_calls


def build_project_understanding(
    file_results: list[dict], manifests: list[dict] | None = None
) -> dict:
    manifests = manifests or []
    frameworks = _framework_inventory(file_results, manifests)
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
        manifests,
    )
    return {
        "project_type": project_type,
        "project_type_status": (
            "CORROBORATED_STATIC"
            if categories
            and all(item["status"] == "CORROBORATED" for item in frameworks)
            else "CANDIDATE"
            if categories else "UNKNOWN"
        ),
        "frameworks": frameworks,
        "routes": routes,
        "authentication_controls": authentication_controls,
        "import_relationships": import_relationships,
        "cross_file_calls": cross_file_calls,
        "manifests": manifests,
        "dependency_declarations": [
            {"manifest": manifest["relative_path"], **dependency}
            for manifest in manifests
            for dependency in manifest["dependencies"]
        ],
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
            "manifests": len(manifests),
            "dependency_declarations": sum(
                len(item["dependencies"]) for item in manifests
            ),
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
            "sca_vulnerability_check": "NOT_RUN",
            "frameworks_require_file_evidence": True,
            "authentication_effectiveness_proven": False,
        },
    }


def _framework_inventory(
    file_results: list[dict], manifests: list[dict]
) -> list[dict]:
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
                    "manifest_evidence_files": [],
                    "evidence_signals": set(),
                },
            )
            item["evidence_files"].append(path)
            item["evidence_signals"].update(framework["evidence"])
            if framework["status"] == "CORROBORATED":
                item["status"] = "CORROBORATED"

    known_names = {"react": "React", "flask": "Flask", "express": "Express"}
    for manifest in manifests:
        for dependency in manifest["dependencies"]:
            framework_name = known_names.get(dependency["name"].casefold())
            if framework_name not in grouped:
                continue
            item = grouped[framework_name]
            item["manifest_evidence_files"].append(
                manifest["relative_path"]
            )
            item["evidence_signals"].add("MANIFEST_DECLARATION")
            item["status"] = "CORROBORATED"

    output = []
    for item in grouped.values():
        item["evidence_files"] = sorted(set(item["evidence_files"]))
        item["manifest_evidence_files"] = sorted(
            set(item["manifest_evidence_files"])
        )
        item["evidence_signals"] = sorted(item["evidence_signals"])
        item["runtime_verified"] = False
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
    manifests: list[dict],
) -> dict:
    nodes = []
    edges = []
    file_ids = {}
    framework_ids = {}
    route_ids = {}

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
        route_ids[
            (
                route["file"],
                route["start_line"],
                route.get("path"),
                tuple(route["methods"]),
            )
        ] = node_id
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

    for manifest in manifests:
        manifest_id = _id(
            "MANIFEST", manifest["relative_path"], manifest["sha256"]
        )
        nodes.append(
            {
                "id": manifest_id,
                "type": "MANIFEST",
                "attributes": {
                    "relative_path": manifest["relative_path"],
                    "status": manifest["status"],
                    "sha256": manifest["sha256"],
                },
            }
        )
        for framework in frameworks:
            if manifest["relative_path"] in framework[
                "manifest_evidence_files"
            ]:
                edges.append(
                    _edge(
                        "SUPPORTS_FRAMEWORK", manifest_id,
                        framework_ids[framework["name"]],
                        {"status": "DECLARED_ONLY"},
                    )
                )
        for dependency in manifest["dependencies"]:
            dependency_id = _id(
                "DEPENDENCY_DECLARATION", manifest["relative_path"],
                dependency["ecosystem"], dependency["name"],
                dependency["scope"],
            )
            nodes.append(
                {
                    "id": dependency_id,
                    "type": "DEPENDENCY_DECLARATION",
                    "attributes": dependency,
                }
            )
            edges.append(
                _edge(
                    "DECLARES_DEPENDENCY", manifest_id, dependency_id,
                    {"status": "DECLARED_ONLY"},
                )
            )

    function_ids = _merge_file_models(
        file_results, nodes, edges, file_ids, framework_ids, route_ids
    )

    for call in cross_file_calls:
        caller_id = function_ids.get(
            (call["source_file"], call["caller_id"])
        )
        callee_id = function_ids.get(
            (call["target_file"], call["callee_id"])
        )
        if caller_id and callee_id:
            edges.append(
                _edge(
                    "CALLS",
                    caller_id,
                    callee_id,
                    {
                        "resolution": call["resolution"],
                        "call_line": call["call_line"],
                        "import_line": call["import_line"],
                    },
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


def _merge_file_models(
    file_results: list[dict],
    nodes: list[dict],
    edges: list[dict],
    file_ids: dict[str, str],
    framework_ids: dict[str, str],
    route_ids: dict[tuple, str],
) -> dict[tuple[str, str], str]:
    function_ids = {}
    for result in file_results:
        path = result["artifact"]["relative_path"]
        model = result["application_model"]
        local_ids = {}
        for node in model["nodes"]:
            kind = node["type"]
            attributes = node["attributes"]
            location = node.get("evidence", {}).get("location", {})
            if kind == "FILE":
                node_id = file_ids[path]
            elif kind == "FRAMEWORK":
                node_id = framework_ids.get(attributes["name"])
            elif kind == "ROUTE":
                node_id = route_ids.get(
                    (
                        path,
                        location.get("start_line"),
                        attributes.get("path"),
                        tuple(attributes.get("methods", [])),
                    )
                )
            else:
                node_id = None
            if node_id is None:
                node_id = _id("FILE_MODEL_NODE", path, node["id"])
                nodes.append(
                    {
                        "id": node_id,
                        "type": kind,
                        "attributes": {"file": path, **attributes},
                        "evidence": node.get("evidence", {}),
                    }
                )
            local_ids[node["id"]] = node_id

        for edge in model["edges"]:
            if edge["type"] in {
                "USES_FRAMEWORK", "EXPOSES_ROUTE", "PROVIDES_ROUTE"
            }:
                continue
            source = local_ids.get(edge["source"])
            target = local_ids.get(edge["target"])
            if source and target:
                edges.append(
                    _edge(
                        edge["type"], source, target,
                        {"file": path, **edge.get("evidence", {})},
                    )
                )

        for symbol in result["relationships"]["symbols"]:
            matches = [
                node for node in model["nodes"]
                if node["type"] == "FUNCTION"
                and node["attributes"].get("qualified_name")
                == symbol["qualified_name"]
                and node.get("evidence", {}).get("location", {}).get(
                    "start_line"
                ) == symbol["start_line"]
            ]
            if len(matches) == 1:
                function_ids[(path, symbol["id"])] = local_ids[
                    matches[0]["id"]
                ]
    return function_ids


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
