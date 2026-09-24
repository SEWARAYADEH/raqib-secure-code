"""Conservative tree-sitter evidence for local JavaScript named imports."""

from __future__ import annotations

from tree_sitter import Parser

from app.parser_engine import JAVASCRIPT_LANGUAGE


def javascript_binding_evidence(source_text: str) -> dict:
    source = source_text.encode("utf-8")
    root = Parser(JAVASCRIPT_LANGUAGE).parse(source).root_node
    if root.has_error:
        return {"safe_calls": [], "exported_functions": []}

    exported_functions = []
    for node in root.named_children:
        if node.type != "export_statement":
            continue
        for child in node.named_children:
            if child.type == "function_declaration":
                name = child.child_by_field_name("name")
                if name is not None:
                    exported_functions.append(_text(name, source))

    leaves = [node for node in _walk(root) if not node.named_children]
    safe_calls = []
    for statement in root.named_children:
        if statement.type != "import_statement":
            continue
        module = next(
            (child for child in statement.named_children if child.type == "string"),
            None,
        )
        if module is None or len(module.named_children) != 1:
            continue
        fragment = module.named_children[0]
        if fragment.type != "string_fragment":
            continue
        module_name = _text(fragment, source)
        for specifier in _walk(statement):
            if specifier.type != "import_specifier":
                continue
            names = specifier.named_children
            if not 1 <= len(names) <= 2 or any(
                name.type != "identifier" for name in names
            ):
                continue
            imported_name = _text(names[0], source)
            binding_node = names[-1]
            binding = _text(binding_node, source)
            calls = []
            valid = True
            for node in leaves:
                if _text(node, source) != binding:
                    continue
                if node == binding_node:
                    continue
                if node.type != "identifier":
                    valid = False
                    break
                call = node.parent
                if (
                    call is None
                    or call.type != "call_expression"
                    or call.child_by_field_name("function") != node
                ):
                    valid = False
                    break
                caller = _top_level_caller(call, root)
                if caller is None:
                    valid = False
                    break
                calls.append({
                    "caller": caller[0],
                    "caller_line": caller[1],
                    "call_line": call.start_point.row + 1,
                })
            if valid:
                for call in calls:
                    safe_calls.append({
                        "import_line": statement.start_point.row + 1,
                        "module": module_name,
                        "imported_name": imported_name,
                        "binding": binding,
                        **call,
                    })
    return {
        "safe_calls": safe_calls,
        "exported_functions": sorted(set(exported_functions)),
    }


def _top_level_caller(call, root) -> tuple[str, int] | None:
    node = call.parent
    while node is not None and node != root:
        if node.type in {
            "function_declaration", "function_expression", "arrow_function",
            "method_definition",
        }:
            if node.type != "function_declaration":
                return None
            parent = node.parent
            if parent is None:
                return None
            if parent.type == "export_statement":
                parent = parent.parent
            if parent != root:
                return None
            name = node.child_by_field_name("name")
            if name is None:
                return None
            return name.text.decode("utf-8"), node.start_point.row + 1
        node = node.parent
    return None


def _walk(node):
    pending = [node]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(reversed(current.named_children))


def _text(node, source: bytes) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8")
