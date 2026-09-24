from __future__ import annotations

from tree_sitter import Language, Parser

import tree_sitter_javascript as ts_javascript
import tree_sitter_python as ts_python


class UnsupportedParserLanguageError(ValueError):
    pass


PYTHON_LANGUAGE = Language(ts_python.language())
JAVASCRIPT_LANGUAGE = Language(ts_javascript.language())


LANGUAGE_CONFIG = {
    "Python": {
        "language": PYTHON_LANGUAGE,
        "family": "python",
    },
    "JavaScript": {
        "language": JAVASCRIPT_LANGUAGE,
        "family": "javascript",
    },
    "JavaScript JSX": {
        "language": JAVASCRIPT_LANGUAGE,
        "family": "javascript",
    },
}


def parse_source(
    source_text: str,
    language: str,
) -> dict:
    if not isinstance(source_text, str):
        raise TypeError("source_text must be a string.")

    config = LANGUAGE_CONFIG.get(language)

    if config is None:
        raise UnsupportedParserLanguageError(
            f"No verified parser is configured for: {language}"
        )

    source_bytes = source_text.encode("utf-8")

    parser = Parser(config["language"])
    tree = parser.parse(source_bytes)

    result = {
        "language": language,
        "parser": "tree-sitter",
        "syntax": _build_syntax_result(
            tree.root_node,
            source_bytes,
        ),
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "assignments": [],
        "control_regions": [],
        "returns": [],
        "decorators": [],
    }

    _walk_tree(
        node=tree.root_node,
        source_bytes=source_bytes,
        family=config["family"],
        result=result,
    )

    result["counts"] = {
        "functions": len(result["functions"]),
        "classes": len(result["classes"]),
        "imports": len(result["imports"]),
        "calls": len(result["calls"]),
        "assignments": len(result["assignments"]),
        "control_regions": len(result["control_regions"]),
        "returns": len(result["returns"]),
        "decorators": len(result["decorators"]),
    }

    return result


def _walk_tree(
    *,
    node,
    source_bytes: bytes,
    family: str,
    result: dict,
) -> None:
    if family == "python":
        _inspect_python_node(
            node,
            source_bytes,
            result,
        )

    elif family == "javascript":
        _inspect_javascript_node(
            node,
            source_bytes,
            result,
        )

    for child in node.named_children:
        _walk_tree(
            node=child,
            source_bytes=source_bytes,
            family=family,
            result=result,
        )


def _inspect_python_node(
    node,
    source_bytes: bytes,
    result: dict,
) -> None:
    if node.type == "decorated_definition":
        definition = node.child_by_field_name("definition")

        if definition is not None:
            for child in node.named_children:
                if child.type != "decorator":
                    continue

                expression = (
                    child.named_children[0]
                    if child.named_children
                    else None
                )
                target_node = expression
                arguments_node = None

                if expression is not None and expression.type == "call":
                    target_node = expression.child_by_field_name(
                        "function"
                    )
                    arguments_node = expression.child_by_field_name(
                        "arguments"
                    )

                if target_node is None:
                    continue

                result["decorators"].append(
                    {
                        "target": _node_text(
                            target_node,
                            source_bytes,
                        ),
                        "arguments": _optional_node_text(
                            arguments_node,
                            source_bytes,
                        ),
                        "argument_values": _argument_values(
                            arguments_node,
                            source_bytes,
                        ),
                        "definition_kind": definition.type,
                        "definition_location": _location(
                            definition
                        ),
                        **_location(child),
                    }
                )

    elif node.type == "function_definition":
        name_node = node.child_by_field_name("name")
        parameters_node = node.child_by_field_name(
            "parameters"
        )

        if name_node is not None:
            result["functions"].append(
                {
                    "name": _node_text(
                        name_node,
                        source_bytes,
                    ),
                    "kind": "function",
                    "parameters": _optional_node_text(
                        parameters_node,
                        source_bytes,
                    ),
                    "parameter_values": _parameter_values(
                        parameters_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )

    elif node.type == "class_definition":
        name_node = node.child_by_field_name("name")

        if name_node is not None:
            result["classes"].append(
                {
                    "name": _node_text(
                        name_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )

    elif node.type in {
        "import_statement",
        "import_from_statement",
    }:
        module_node = (
            node.child_by_field_name("module_name")
            or node.child_by_field_name("name")
        )
        result["imports"].append(
            {
                "statement": _node_text(
                    node,
                    source_bytes,
                ),
                "module": (
                    _node_text(module_node, source_bytes)
                    if module_node is not None
                    else None
                ),
                "kind": node.type,
                **_location(node),
            }
        )

    elif node.type == "assignment":
        left_node = node.child_by_field_name("left")
        right_node = node.child_by_field_name("right")

        if left_node is not None and right_node is not None:
            result["assignments"].append(
                {
                    "target": _node_text(
                        left_node,
                        source_bytes,
                    ),
                    "value": _node_text(
                        right_node,
                        source_bytes,
                    ),
                    "kind": "assignment",
                    "target_location": _location(left_node),
                    "value_location": _location(right_node),
                    **_location(node),
                }
            )

    elif node.type == "if_statement":
        _inspect_python_if_statement(
            node,
            source_bytes,
            result,
        )

    elif node.type == "return_statement":
        _append_return(
            node,
            source_bytes,
            result,
        )

    elif node.type == "call":
        function_node = node.child_by_field_name(
            "function"
        )
        arguments_node = node.child_by_field_name(
            "arguments"
        )

        if function_node is not None:
            result["calls"].append(
                {
                    "target": _node_text(
                        function_node,
                        source_bytes,
                    ),
                    "arguments": _optional_node_text(
                        arguments_node,
                        source_bytes,
                    ),
                    "argument_values": _argument_values(
                        arguments_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )


def _inspect_javascript_node(
    node,
    source_bytes: bytes,
    result: dict,
) -> None:
    if node.type in {
        "function_declaration",
        "generator_function_declaration",
    }:
        name_node = node.child_by_field_name("name")
        parameters_node = node.child_by_field_name(
            "parameters"
        )

        if name_node is not None:
            result["functions"].append(
                {
                    "name": _node_text(
                        name_node,
                        source_bytes,
                    ),
                    "kind": "function",
                    "parameters": _optional_node_text(
                        parameters_node,
                        source_bytes,
                    ),
                    "parameter_values": _parameter_values(
                        parameters_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )

    elif node.type == "method_definition":
        name_node = node.child_by_field_name("name")
        parameters_node = node.child_by_field_name(
            "parameters"
        )

        if name_node is not None:
            result["functions"].append(
                {
                    "name": _node_text(
                        name_node,
                        source_bytes,
                    ),
                    "kind": "method",
                    "parameters": _optional_node_text(
                        parameters_node,
                        source_bytes,
                    ),
                    "parameter_values": _parameter_values(
                        parameters_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )

    elif node.type == "variable_declarator":
        name_node = node.child_by_field_name("name")
        value_node = node.child_by_field_name("value")

        if name_node is not None and value_node is not None:
            if value_node.type in {
                "arrow_function",
                "function_expression",
            }:
                parameters_node = (
                    value_node.child_by_field_name(
                        "parameters"
                    )
                )
                result["functions"].append(
                    {
                        "name": _node_text(
                            name_node,
                            source_bytes,
                        ),
                        "kind": value_node.type,
                        "parameters": (
                            _optional_node_text(
                                parameters_node,
                                source_bytes,
                            )
                        ),
                        "parameter_values": _parameter_values(
                            parameters_node,
                            source_bytes,
                        ),
                        **_location(node),
                    }
                )
            else:
                result["assignments"].append(
                    {
                        "target": _node_text(
                            name_node,
                            source_bytes,
                        ),
                        "value": _node_text(
                            value_node,
                            source_bytes,
                        ),
                        "kind": "variable_declaration",
                        "target_location": _location(name_node),
                        "value_location": _location(value_node),
                        **_location(node),
                    }
                )

    elif node.type == "assignment_expression":
        left_node = node.child_by_field_name("left")
        right_node = node.child_by_field_name("right")

        if left_node is not None and right_node is not None:
            result["assignments"].append(
                {
                    "target": _node_text(
                        left_node,
                        source_bytes,
                    ),
                    "value": _node_text(
                        right_node,
                        source_bytes,
                    ),
                    "kind": "assignment",
                    "target_location": _location(left_node),
                    "value_location": _location(right_node),
                    **_location(node),
                }
            )

    elif node.type == "if_statement":
        _inspect_javascript_if_statement(
            node,
            source_bytes,
            result,
        )

    elif node.type == "return_statement":
        _append_return(
            node,
            source_bytes,
            result,
        )

    elif node.type == "class_declaration":
        name_node = node.child_by_field_name("name")

        if name_node is not None:
            result["classes"].append(
                {
                    "name": _node_text(
                        name_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )

    elif node.type == "import_statement":
        source_node = node.child_by_field_name("source")
        result["imports"].append(
            {
                "statement": _node_text(
                    node,
                    source_bytes,
                ),
                "module": (
                    _literal_node_value(source_node, source_bytes)
                    if source_node is not None
                    else None
                ),
                "kind": node.type,
                **_location(node),
            }
        )

    elif node.type == "call_expression":
        function_node = node.child_by_field_name(
            "function"
        )
        arguments_node = node.child_by_field_name(
            "arguments"
        )

        if function_node is not None:
            result["calls"].append(
                {
                    "target": _node_text(
                        function_node,
                        source_bytes,
                    ),
                    "arguments": _optional_node_text(
                        arguments_node,
                        source_bytes,
                    ),
                    "argument_values": _argument_values(
                        arguments_node,
                        source_bytes,
                    ),
                    **_location(node),
                }
            )


def _build_syntax_result(
    root_node,
    source_bytes: bytes,
) -> dict:
    errors = []

    _collect_syntax_errors(
        root_node,
        source_bytes,
        errors,
    )

    return {
        "valid": not root_node.has_error,
        "error_count": len(errors),
        "errors": errors,
    }


def _inspect_python_if_statement(
    node,
    source_bytes: bytes,
    result: dict,
) -> None:
    group_id = _control_group_id(node)
    consequence = node.child_by_field_name("consequence")
    condition = node.child_by_field_name("condition")

    _append_control_region(
        result=result,
        group_id=group_id,
        branch_index=0,
        kind="IF",
        condition_node=condition,
        body_node=consequence,
        source_bytes=source_bytes,
    )

    branch_index = 1

    for child in node.named_children:
        if child.type == "elif_clause":
            _append_control_region(
                result=result,
                group_id=group_id,
                branch_index=branch_index,
                kind="ELIF",
                condition_node=child.child_by_field_name(
                    "condition"
                ),
                body_node=child.child_by_field_name(
                    "consequence"
                ),
                source_bytes=source_bytes,
            )
            branch_index += 1
        elif child.type == "else_clause":
            _append_control_region(
                result=result,
                group_id=group_id,
                branch_index=branch_index,
                kind="ELSE",
                condition_node=None,
                body_node=child.child_by_field_name("body"),
                source_bytes=source_bytes,
            )


def _inspect_javascript_if_statement(
    node,
    source_bytes: bytes,
    result: dict,
) -> None:
    group_id = _control_group_id(node)
    consequence = node.child_by_field_name("consequence")
    condition = node.child_by_field_name("condition")

    _append_control_region(
        result=result,
        group_id=group_id,
        branch_index=0,
        kind="IF",
        condition_node=condition,
        body_node=consequence,
        source_bytes=source_bytes,
    )
    alternative = node.child_by_field_name("alternative")

    if alternative is not None:
        _append_control_region(
            result=result,
            group_id=group_id,
            branch_index=1,
            kind="ELSE",
            condition_node=None,
            body_node=alternative,
            source_bytes=source_bytes,
        )


def _append_control_region(
    *,
    result: dict,
    group_id: str,
    branch_index: int,
    kind: str,
    condition_node,
    body_node,
    source_bytes: bytes,
) -> None:
    if body_node is None:
        return

    result["control_regions"].append(
        {
            "group_id": group_id,
            "branch_id": f"{group_id}:{branch_index}",
            "branch_index": branch_index,
            "kind": kind,
            "condition": _optional_node_text(
                condition_node,
                source_bytes,
            ),
            **_location(body_node),
        }
    )


def _control_group_id(node) -> str:
    return (
        "branch:"
        f"{node.start_point.row + 1}:"
        f"{node.start_point.column}:"
        f"{node.end_point.row + 1}:"
        f"{node.end_point.column}"
    )


def _collect_syntax_errors(
    node,
    source_bytes: bytes,
    errors: list,
) -> None:
    if len(errors) >= 20:
        return

    is_missing = getattr(
        node,
        "is_missing",
        False,
    )

    if node.type == "ERROR" or is_missing:
        errors.append(
            {
                "type": node.type,
                "text": _node_text(
                    node,
                    source_bytes,
                )[:200],
                **_location(node),
            }
        )

    for child in node.children:
        _collect_syntax_errors(
            child,
            source_bytes,
            errors,
        )


def _location(node) -> dict:
    return {
        "start_line": node.start_point.row + 1,
        "end_line": node.end_point.row + 1,
        "start_column": node.start_point.column,
        "end_column": node.end_point.column,
    }


def _node_text(
    node,
    source_bytes: bytes,
) -> str:
    return source_bytes[
        node.start_byte : node.end_byte
    ].decode(
        "utf-8",
        errors="replace",
    )


def _literal_node_value(node, source_bytes: bytes) -> str | None:
    value = _node_text(node, source_bytes)
    if len(value) < 2 or value[0] not in {"'", '"', "`"}:
        return None
    if value[-1] != value[0]:
        return None
    return value[1:-1]


def _optional_node_text(
    node,
    source_bytes: bytes,
) -> str | None:
    if node is None:
        return None

    return _node_text(
        node,
        source_bytes,
    )


def _argument_values(
    arguments_node,
    source_bytes: bytes,
) -> list[dict]:
    if arguments_node is None:
        return []

    return [
        {
            "text": _node_text(
                child,
                source_bytes,
            ),
            **_location(child),
        }
        for child in arguments_node.named_children
    ]


def _parameter_values(
    parameters_node,
    source_bytes: bytes,
) -> list[dict]:
    if parameters_node is None:
        return []

    return [
        {
            "text": _node_text(child, source_bytes),
            **_location(child),
        }
        for child in parameters_node.named_children
    ]


def _append_return(
    node,
    source_bytes: bytes,
    result: dict,
) -> None:
    value_node = (
        node.named_children[0]
        if node.named_children
        else None
    )
    result["returns"].append(
        {
            "value": _optional_node_text(
                value_node,
                source_bytes,
            ),
            "value_location": (
                _location(value_node)
                if value_node is not None
                else None
            ),
            **_location(node),
        }
    )
