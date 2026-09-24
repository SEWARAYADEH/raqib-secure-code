from __future__ import annotations

import hashlib
import json
from collections import Counter


def build_application_model(
    *,
    artifact: dict,
    parsed: dict,
    relationships: dict,
    semantics: dict,
    data_flow: dict,
    control_flow: dict,
    understanding: dict,
) -> dict:
    builder = _ModelBuilder(artifact)
    file_id = builder.add_node(
        node_type="FILE",
        identity=[artifact["sha256"]],
        attributes={
            "filename": artifact["filename"],
            "language": parsed["language"],
            "sha256": artifact["sha256"],
            "size_bytes": artifact["size_bytes"],
        },
    )

    class_ids = _add_classes(
        builder,
        file_id,
        parsed,
    )
    function_ids = _add_functions(
        builder,
        file_id,
        class_ids,
        relationships,
    )
    understanding_ids = _add_application_understanding(
        builder,
        file_id,
        function_ids,
        relationships,
        understanding,
    )
    call_ids = _add_calls(
        builder,
        file_id,
        function_ids,
        parsed,
        relationships,
    )
    _add_assignments(
        builder,
        file_id,
        function_ids,
        parsed,
        relationships,
    )
    _add_control_regions(
        builder,
        file_id,
        function_ids,
        control_flow,
        relationships,
    )
    _add_local_call_edges(
        builder,
        function_ids,
        relationships,
    )
    semantic_ids = _add_semantics(
        builder,
        file_id,
        call_ids,
        semantics,
    )
    _link_route_security_context(
        builder,
        understanding_ids,
        semantic_ids,
        semantics,
        relationships,
    )
    _add_data_flow_paths(
        builder,
        file_id,
        semantic_ids,
        data_flow,
    )

    return builder.build()


def _add_application_understanding(
    builder: _ModelBuilder,
    file_id: str,
    function_ids: dict[str, str],
    relationships: dict,
    understanding: dict,
) -> dict:
    framework_ids = {}
    for framework in understanding.get("frameworks", []):
        node_id = builder.add_node(
            node_type="FRAMEWORK",
            identity=[framework["name"]],
            attributes=framework,
        )
        framework_ids[framework["name"]] = node_id
        builder.add_edge(
            edge_type="USES_FRAMEWORK",
            source_id=file_id,
            target_id=node_id,
            evidence={"signals": framework["evidence"]},
        )

    for dependency in understanding.get("dependencies", []):
        dependency_id = builder.add_node(
            node_type="DEPENDENCY_IMPORT",
            identity=[dependency.get("module"), dependency["start_line"]],
            attributes={
                key: value
                for key, value in dependency.items()
                if key not in {
                    "start_line",
                    "end_line",
                    "start_column",
                    "end_column",
                }
            },
            location=dependency,
        )
        builder.add_edge(
            edge_type="IMPORTS_DEPENDENCY",
            source_id=file_id,
            target_id=dependency_id,
            evidence={"origin": "UNRESOLVED"},
        )

    for service in understanding.get("services", []):
        service_id = builder.add_node(
            node_type="SERVICE_INSTANCE",
            identity=[service["variable"], service["start_line"]],
            attributes={
                key: value
                for key, value in service.items()
                if key not in {
                    "start_line",
                    "end_line",
                    "start_column",
                    "end_column",
                }
            },
            location=service,
        )
        builder.add_edge(
            edge_type="DECLARES_SERVICE",
            source_id=file_id,
            target_id=service_id,
            evidence={"resolution": service["resolution"]},
        )

    symbols = relationships.get("symbols", [])
    for operation in understanding.get("database_operations", []):
        operation_id = builder.add_node(
            node_type="DATABASE_OPERATION",
            identity=[
                operation["target"],
                operation["start_line"],
                operation["start_column"],
            ],
            attributes={
                key: value
                for key, value in operation.items()
                if key not in {
                    "start_line",
                    "end_line",
                    "start_column",
                    "end_column",
                }
            },
            location=operation,
        )
        owner = _containing_symbol(operation, symbols)
        owner_id = (
            function_ids.get(owner["id"], file_id)
            if owner
            else file_id
        )
        builder.add_edge(
            edge_type="PERFORMS_DATABASE_OPERATION",
            source_id=owner_id,
            target_id=operation_id,
            evidence={
                "status": operation["status"],
                "resource": operation["resource"],
            },
        )
    functions_by_name: dict[str, list[str]] = {}
    symbol_ids_by_name: dict[str, list[str]] = {}
    for symbol in symbols:
        model_id = function_ids.get(symbol["id"])
        if model_id:
            functions_by_name.setdefault(symbol["name"], []).append(model_id)
            symbol_ids_by_name.setdefault(symbol["name"], []).append(symbol["id"])

    route_ids = []

    for route in understanding.get("routes", []):
        route_id = builder.add_node(
            node_type="ROUTE",
            identity=[
                route["framework"],
                route.get("path"),
                route["methods"],
                route["start_line"],
            ],
            attributes={
                key: value
                for key, value in route.items()
                if key not in {
                    "start_line",
                    "end_line",
                    "start_column",
                    "end_column",
                }
            },
            location=route,
        )
        builder.add_edge(
            edge_type="EXPOSES_ROUTE",
            source_id=file_id,
            target_id=route_id,
        )
        handler_symbol_id = None
        framework_id = framework_ids.get(route["framework"])
        if framework_id:
            builder.add_edge(
                edge_type="PROVIDES_ROUTE",
                source_id=framework_id,
                target_id=route_id,
            )

        candidates = functions_by_name.get(route.get("handler"), [])
        if len(candidates) == 1:
            builder.add_edge(
                edge_type="HANDLED_BY",
                source_id=route_id,
                target_id=candidates[0],
                evidence={"resolution": "EXACT_LOCAL_SYMBOL"},
            )
            symbol_candidates = symbol_ids_by_name.get(route.get("handler"), [])
            if len(symbol_candidates) == 1:
                handler_symbol_id = symbol_candidates[0]
        route_ids.append(
            {
                "route_id": route_id,
                "handler_symbol_id": handler_symbol_id,
            }
        )

    for control in understanding.get("authentication_controls", []):
        control_id = builder.add_node(
            node_type="AUTHENTICATION_CONTROL",
            identity=[
                control["target"],
                control.get("handler"),
                control["start_line"],
            ],
            attributes={
                key: value
                for key, value in control.items()
                if key not in {
                    "start_line",
                    "end_line",
                    "start_column",
                    "end_column",
                }
            },
            location=control,
        )
        builder.add_edge(
            edge_type="OBSERVES_CONTROL",
            source_id=file_id,
            target_id=control_id,
        )
        candidates = functions_by_name.get(control.get("handler"), [])
        if len(candidates) == 1:
            builder.add_edge(
                edge_type="GUARDS",
                source_id=control_id,
                target_id=candidates[0],
                evidence={"effectiveness": "UNVERIFIED"},
            )

    return {"routes": route_ids}


def _link_route_security_context(
    builder: _ModelBuilder,
    understanding_ids: dict,
    semantic_ids: dict[tuple, str],
    semantics: dict,
    relationships: dict,
) -> None:
    symbols = {
        item["id"]: item
        for item in relationships.get("symbols", [])
    }
    for route in understanding_ids.get("routes", []):
        handler = symbols.get(route["handler_symbol_id"])
        if handler is None:
            continue
        for observation in semantics.get("observations", []):
            if not _contains(handler, observation):
                continue
            semantic_id = semantic_ids.get(_semantic_key(observation))
            if semantic_id is None:
                continue
            edge_type = {
                "SOURCE": "ACCEPTS_INPUT_FROM",
                "SINK": "REACHES_SENSITIVE_OPERATION",
                "SECURITY_CONTROL": "OBSERVES_SECURITY_CONTROL",
            }.get(observation["kind"])
            if edge_type:
                builder.add_edge(
                    edge_type=edge_type,
                    source_id=route["route_id"],
                    target_id=semantic_id,
                    evidence={
                        "scope": "EXACT_HANDLER_BODY",
                        "effectiveness": (
                            "UNVERIFIED"
                            if observation["kind"] == "SECURITY_CONTROL"
                            else None
                        ),
                    },
                )


class _ModelBuilder:
    def __init__(self, artifact: dict):
        self.artifact = artifact
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._node_ids: set[str] = set()
        self._edge_ids: set[str] = set()

    def add_node(
        self,
        *,
        node_type: str,
        identity: list,
        attributes: dict,
        location: dict | None = None,
    ) -> str:
        node_id = _stable_id(
            "node",
            node_type,
            self.artifact["sha256"],
            *identity,
        )

        if node_id in self._node_ids:
            return node_id

        node = {
            "id": node_id,
            "type": node_type,
            "attributes": attributes,
            "evidence": {
                "artifact_sha256": self.artifact["sha256"],
            },
        }

        if location is not None:
            node["evidence"]["location"] = _location(location)

        self.nodes.append(node)
        self._node_ids.add(node_id)
        return node_id

    def add_edge(
        self,
        *,
        edge_type: str,
        source_id: str,
        target_id: str,
        evidence: dict | None = None,
    ) -> str:
        edge_id = _stable_id(
            "edge",
            edge_type,
            source_id,
            target_id,
            evidence or {},
        )

        if edge_id in self._edge_ids:
            return edge_id

        self.edges.append(
            {
                "id": edge_id,
                "type": edge_type,
                "source": source_id,
                "target": target_id,
                "evidence": evidence or {},
            }
        )
        self._edge_ids.add(edge_id)
        return edge_id

    def build(self) -> dict:
        node_counts = Counter(
            node["type"] for node in self.nodes
        )
        edge_counts = Counter(
            edge["type"] for edge in self.edges
        )

        return {
            "schema_version": "1.0",
            "nodes": self.nodes,
            "edges": self.edges,
            "counts": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "nodes_by_type": dict(sorted(node_counts.items())),
                "edges_by_type": dict(sorted(edge_counts.items())),
            },
            "claims": {
                "scope": "SINGLE_FILE_STATIC_MODEL",
                "vulnerabilities_declared": 0,
            },
        }


def _add_classes(
    builder: _ModelBuilder,
    file_id: str,
    parsed: dict,
) -> dict[tuple, str]:
    class_ids = {}

    for item in parsed.get("classes", []):
        key = _symbol_key(item)
        node_id = builder.add_node(
            node_type="CLASS",
            identity=list(key),
            attributes={"name": item["name"]},
            location=item,
        )
        class_ids[key] = node_id
        builder.add_edge(
            edge_type="DECLARES",
            source_id=file_id,
            target_id=node_id,
        )

    return class_ids


def _add_functions(
    builder: _ModelBuilder,
    file_id: str,
    class_ids: dict[tuple, str],
    relationships: dict,
) -> dict[str, str]:
    function_ids = {}
    classes_by_id = {
        item["id"]: item
        for item in relationships.get("classes", [])
    }

    for symbol in relationships.get("symbols", []):
        node_id = builder.add_node(
            node_type="FUNCTION",
            identity=[
                symbol["qualified_name"],
                symbol["start_line"],
                symbol["start_column"],
            ],
            attributes={
                "name": symbol["name"],
                "qualified_name": symbol["qualified_name"],
                "kind": symbol["kind"],
                "parameters": symbol.get("parameters"),
            },
            location=symbol,
        )
        function_ids[symbol["id"]] = node_id
        parent_id = file_id

        if symbol.get("class_id"):
            class_item = classes_by_id.get(symbol["class_id"])

            if class_item is not None:
                parent_id = class_ids.get(
                    _symbol_key(class_item),
                    file_id,
                )

        builder.add_edge(
            edge_type="DECLARES",
            source_id=parent_id,
            target_id=node_id,
        )

    return function_ids


def _add_calls(
    builder: _ModelBuilder,
    file_id: str,
    function_ids: dict[str, str],
    parsed: dict,
    relationships: dict,
) -> dict[tuple, str]:
    call_ids = {}
    symbols = relationships.get("symbols", [])

    for call in parsed.get("calls", []):
        key = _call_key(call)
        node_id = builder.add_node(
            node_type="CALL",
            identity=list(key),
            attributes={
                "target": call["target"],
                "arguments": call.get("arguments"),
            },
            location=call,
        )
        call_ids[key] = node_id
        owner = _containing_symbol(call, symbols)
        parent_id = (
            function_ids.get(owner["id"], file_id)
            if owner
            else file_id
        )
        builder.add_edge(
            edge_type="CONTAINS_CALL",
            source_id=parent_id,
            target_id=node_id,
        )

    return call_ids


def _add_assignments(
    builder: _ModelBuilder,
    file_id: str,
    function_ids: dict[str, str],
    parsed: dict,
    relationships: dict,
) -> None:
    symbols = relationships.get("symbols", [])

    for item in parsed.get("assignments", []):
        node_id = builder.add_node(
            node_type="ASSIGNMENT",
            identity=[
                item["target"],
                item["start_line"],
                item["start_column"],
            ],
            attributes={
                "target": item["target"],
                "value": item["value"],
                "kind": item["kind"],
            },
            location=item,
        )
        owner = _containing_symbol(item, symbols)
        parent_id = (
            function_ids.get(owner["id"], file_id)
            if owner
            else file_id
        )
        builder.add_edge(
            edge_type="CONTAINS_ASSIGNMENT",
            source_id=parent_id,
            target_id=node_id,
        )


def _add_local_call_edges(
    builder: _ModelBuilder,
    function_ids: dict[str, str],
    relationships: dict,
) -> None:
    for item in relationships.get("relationships", []):
        source_id = function_ids.get(item["caller_id"])
        target_id = function_ids.get(item["callee_id"])

        if source_id is None or target_id is None:
            continue

        builder.add_edge(
            edge_type="CALLS",
            source_id=source_id,
            target_id=target_id,
            evidence={
                "call_target": item["call_target"],
                "line": item["line"],
                "resolution": item["resolution"],
            },
        )


def _add_control_regions(
    builder: _ModelBuilder,
    file_id: str,
    function_ids: dict[str, str],
    control_flow: dict,
    relationships: dict,
) -> None:
    symbols = relationships.get("symbols", [])

    for region in control_flow.get("regions", []):
        node_id = builder.add_node(
            node_type="CONTROL_BRANCH",
            identity=[region["branch_id"]],
            attributes={
                "group_id": region["group_id"],
                "branch_id": region["branch_id"],
                "kind": region["kind"],
                "condition": region["condition"],
            },
            location=region,
        )
        owner = _containing_symbol(region, symbols)
        parent_id = (
            function_ids.get(owner["id"], file_id)
            if owner
            else file_id
        )
        builder.add_edge(
            edge_type="CONTAINS_CONTROL_REGION",
            source_id=parent_id,
            target_id=node_id,
        )


def _add_semantics(
    builder: _ModelBuilder,
    file_id: str,
    call_ids: dict[tuple, str],
    semantics: dict,
) -> dict[tuple, str]:
    semantic_ids = {}

    for item in semantics.get("observations", []):
        key = _semantic_key(item)
        node_id = builder.add_node(
            node_type=item["kind"],
            identity=list(key),
            attributes={
                "rule_id": item["rule_id"],
                "category": item["category"],
                "target": item["target"],
                "evidence_strength": item[
                    "evidence_strength"
                ],
            },
            location=item,
        )
        semantic_ids[key] = node_id
        call_id = call_ids.get(_call_key(item))
        builder.add_edge(
            edge_type="OBSERVED_AT",
            source_id=node_id,
            target_id=call_id or file_id,
        )

    return semantic_ids


def _add_data_flow_paths(
    builder: _ModelBuilder,
    file_id: str,
    semantic_ids: dict[tuple, str],
    data_flow: dict,
) -> None:
    for index, path in enumerate(data_flow.get("paths", [])):
        path_id = builder.add_node(
            node_type="EVIDENCE_PATH",
            identity=[
                index,
                path["source"]["rule_id"],
                path["sink"]["rule_id"],
                path["scope"]["start_line"],
            ],
            attributes={
                "kind": path["kind"],
                "status": path["status"],
                "scope": path["scope"],
                "trace": path["trace"],
                "evidence_strength": path[
                    "evidence_strength"
                ],
            },
        )
        source_id = semantic_ids.get(
            _semantic_key(path["source"])
        )
        sink_id = semantic_ids.get(
            _semantic_key(path["sink"])
        )

        builder.add_edge(
            edge_type="CONTAINS_EVIDENCE",
            source_id=file_id,
            target_id=path_id,
        )

        if source_id:
            builder.add_edge(
                edge_type="PATH_STARTS_AT",
                source_id=path_id,
                target_id=source_id,
            )

        if sink_id:
            builder.add_edge(
                edge_type="PATH_ENDS_AT",
                source_id=path_id,
                target_id=sink_id,
            )


def _containing_symbol(
    item: dict,
    symbols: list,
) -> dict | None:
    candidates = [
        symbol
        for symbol in symbols
        if _contains(symbol, item)
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda symbol: (
            symbol["end_line"] - symbol["start_line"],
            symbol["end_column"] - symbol["start_column"],
        ),
    )


def _contains(outer: dict, inner: dict) -> bool:
    return (
        (outer["start_line"], outer["start_column"])
        <= (inner["start_line"], inner["start_column"])
        and (outer["end_line"], outer["end_column"])
        >= (inner["end_line"], inner["end_column"])
    )


def _symbol_key(item: dict) -> tuple:
    return (
        item["name"],
        item["start_line"],
        item["start_column"],
    )


def _call_key(item: dict) -> tuple:
    return (
        item["target"],
        item["start_line"],
        item["start_column"],
        item["end_line"],
        item["end_column"],
    )


def _semantic_key(item: dict) -> tuple:
    return (
        item["rule_id"],
        item["target"],
        item["start_line"],
        item.get("start_column", 0),
        item["end_line"],
        item.get("end_column", 0),
    )


def _location(item: dict) -> dict:
    return {
        "start_line": item["start_line"],
        "end_line": item["end_line"],
        "start_column": item["start_column"],
        "end_column": item["end_column"],
    }


def _stable_id(namespace: str, *parts) -> str:
    encoded = json.dumps(
        parts,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:24]
    return f"{namespace}:{digest}"
