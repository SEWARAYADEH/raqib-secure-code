"""Resolve only statically bound, unshadowed Python cross-file calls."""

from __future__ import annotations

import ast
import symtable


def python_binding_evidence(source_text: str) -> dict:
    """Record imports whose bindings cannot be reassigned in this source."""
    try:
        tree = ast.parse(source_text)
        symbols = symtable.symtable(source_text, "<uploaded>", "exec")
    except (SyntaxError, ValueError):
        return {"safe_imports": [], "global_callers": []}

    writes = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and isinstance(node.ctx, (ast.Store, ast.Del))
    }
    writes.update(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar))
        and node.name
    )
    writes.update(
        node.rest
        for node in ast.walk(tree)
        if isinstance(node, ast.MatchMapping) and node.rest
    )
    declarations = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    import_bindings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            import_bindings.extend(
                alias.asname or alias.name for alias in node.names
            )
        elif isinstance(node, ast.Import):
            import_bindings.extend(
                alias.asname or alias.name.split(".", 1)[0]
                for alias in node.names
            )

    safe_imports = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level:
            continue
        for alias in node.names:
            binding = alias.asname or alias.name
            if (
                alias.name != "*"
                and import_bindings.count(binding) == 1
                and binding not in writes
                and binding not in declarations
            ):
                safe_imports.append(
                    {
                        "line": node.lineno,
                        "module": node.module,
                        "imported_name": alias.name,
                        "binding": binding,
                    }
                )

    global_callers = []
    for child in symbols.get_children():
        if child.get_type() != "function":
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if (
                node.name != child.get_name()
                or node.lineno != child.get_lineno()
            ):
                continue
            for binding in (item["binding"] for item in safe_imports):
                if (
                    binding in child.get_identifiers()
                    and child.lookup(binding).is_global()
                ):
                    global_callers.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "binding": binding,
                        }
                    )
    return {"safe_imports": safe_imports, "global_callers": global_callers}


def resolve_project_calls(
    file_results: list[dict], import_relationships: list[dict]
) -> list[dict]:
    files = {item["artifact"]["relative_path"]: item for item in file_results}
    resolved = []

    for relationship in import_relationships:
        if relationship["status"] != "RESOLVED":
            continue
        source_file = relationship["source_file"]
        target_file = relationship["target_file"]
        source = files[source_file]
        target = files[target_file]
        if (
            source["language"]["candidate"] in {"JavaScript", "JavaScript JSX"}
            and target["language"]["candidate"]
            in {"JavaScript", "JavaScript JSX"}
        ):
            resolved.extend(
                _resolve_javascript_calls(
                    relationship, source_file, target_file, source, target
                )
            )
            continue
        if (
            source["language"]["candidate"] != "Python"
            or target["language"]["candidate"] != "Python"
        ):
            continue

        imports = [
            item
            for item in source["structure"]["imports"]
            if item["start_line"] == relationship["line"]
            and item["kind"] == "import_from_statement"
        ]
        for imported in imports:
            try:
                statement = ast.parse(imported["statement"]).body[0]
            except SyntaxError:
                continue
            if not isinstance(statement, ast.ImportFrom) or statement.level:
                continue
            if statement.module != relationship["module"]:
                continue

            for alias in statement.names:
                if alias.name == "*":
                    continue
                binding = alias.asname or alias.name
                proof = source.get("python_binding_evidence", {})
                if not any(
                    item == {
                        "line": relationship["line"],
                        "module": relationship["module"],
                        "imported_name": alias.name,
                        "binding": binding,
                    }
                    for item in proof.get("safe_imports", [])
                ):
                    continue
                targets = [
                    symbol
                    for symbol in target["relationships"]["symbols"]
                    if symbol["name"] == alias.name
                    and symbol["parent_function_id"] is None
                    and symbol["class_id"] is None
                    and symbol["start_column"] == 0
                ]
                if len(targets) != 1:
                    continue

                for call in source["relationships"]["unresolved_calls"]:
                    if call["call_target"] != binding:
                        continue
                    callers = [
                        symbol
                        for symbol in source["relationships"]["symbols"]
                        if symbol["id"] == call["caller_id"]
                    ]
                    if len(callers) != 1 or not any(
                        item == {
                            "name": callers[0]["name"],
                            "line": callers[0]["start_line"],
                            "binding": binding,
                        }
                        for item in proof.get("global_callers", [])
                    ):
                        continue
                    resolved.append(
                        {
                            "source_file": source_file,
                            "caller": call["caller"],
                            "caller_id": call["caller_id"],
                            "target_file": target_file,
                            "callee": targets[0]["qualified_name"],
                            "callee_id": targets[0]["id"],
                            "call_line": call["line"],
                            "import_line": relationship["line"],
                            "resolution": "STATIC_PYTHON_FROM_IMPORT",
                        }
                    )

    return sorted(
        resolved,
        key=lambda item: (
            item["source_file"],
            item["call_line"],
            item["target_file"],
        ),
    )


def _resolve_javascript_calls(
    relationship: dict,
    source_file: str,
    target_file: str,
    source: dict,
    target: dict,
) -> list[dict]:
    source_proof = source.get("javascript_binding_evidence") or {}
    target_proof = target.get("javascript_binding_evidence") or {}
    resolved = []
    for proof in source_proof.get("safe_calls", []):
        if (
            proof["import_line"] != relationship["line"]
            or proof["module"] != relationship["module"]
            or proof["imported_name"]
            not in target_proof.get("exported_functions", [])
        ):
            continue
        targets = [
            symbol
            for symbol in target["relationships"]["symbols"]
            if symbol["name"] == proof["imported_name"]
            and symbol["parent_function_id"] is None
            and symbol["class_id"] is None
        ]
        callers = [
            symbol
            for symbol in source["relationships"]["symbols"]
            if symbol["name"] == proof["caller"]
            and symbol["start_line"] == proof["caller_line"]
            and symbol["parent_function_id"] is None
            and symbol["class_id"] is None
        ]
        calls = [
            call
            for call in source["relationships"]["unresolved_calls"]
            if call["call_target"] == proof["binding"]
            and call["line"] == proof["call_line"]
            and callers
            and call["caller_id"] == callers[0]["id"]
        ]
        if len(targets) != 1 or len(callers) != 1 or len(calls) != 1:
            continue
        resolved.append(
            {
                "source_file": source_file,
                "caller": callers[0]["qualified_name"],
                "caller_id": callers[0]["id"],
                "target_file": target_file,
                "callee": targets[0]["qualified_name"],
                "callee_id": targets[0]["id"],
                "call_line": proof["call_line"],
                "import_line": relationship["line"],
                "resolution": "STATIC_JAVASCRIPT_NAMED_IMPORT",
            }
        )
    return resolved
