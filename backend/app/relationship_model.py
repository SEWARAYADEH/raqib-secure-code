from __future__ import annotations


RESOLUTION_LOCAL = "LOCAL"
RESOLUTION_AMBIGUOUS = "AMBIGUOUS"
RESOLUTION_UNRESOLVED = "UNRESOLVED"


def build_relationship_model(parsed: dict) -> dict:
    functions = [
        _build_function_symbol(item, index)
        for index, item in enumerate(
            parsed.get("functions", [])
        )
    ]

    classes = [
        _build_class_symbol(item, index)
        for index, item in enumerate(
            parsed.get("classes", [])
        )
    ]

    _attach_containers(
        functions,
        classes,
    )

    _assign_qualified_names(functions)

    relationships = []
    unresolved_calls = []
    module_calls = []

    for call in parsed.get("calls", []):
        caller = _find_containing_function(
            call,
            functions,
        )

        if caller is None:
            module_calls.append(
                _build_unresolved_call(
                    call,
                    caller=None,
                )
            )
            continue

        resolution = _resolve_call(
            call_target=call["target"],
            caller=caller,
            functions=functions,
            classes=classes,
        )

        if resolution["status"] == RESOLUTION_LOCAL:
            callee = resolution["symbol"]

            relationships.append(
                {
                    "caller_id": caller["id"],
                    "caller": caller["qualified_name"],
                    "callee_id": callee["id"],
                    "callee": callee["qualified_name"],
                    "call_target": call["target"],
                    "resolution": RESOLUTION_LOCAL,
                    "line": call["start_line"],
                }
            )

        else:
            unresolved_calls.append(
                {
                    **_build_unresolved_call(
                        call,
                        caller=caller,
                    ),
                    "resolution": resolution["status"],
                }
            )

    return {
        "symbols": functions,
        "classes": classes,
        "relationships": relationships,
        "unresolved_calls": unresolved_calls,
        "module_calls": module_calls,
        "counts": {
            "functions": len(functions),
            "classes": len(classes),
            "local_relationships": len(
                relationships
            ),
            "unresolved_calls": len(
                unresolved_calls
            ),
            "module_calls": len(module_calls),
        },
    }


def _build_function_symbol(
    item: dict,
    index: int,
) -> dict:
    return {
        "id": (
            f"function:{index}:"
            f"{item['start_line']}:"
            f"{item['start_column']}"
        ),
        "name": item["name"],
        "kind": item.get(
            "kind",
            "function",
        ),
        "parameters": item.get("parameters"),
        "parameter_values": item.get(
            "parameter_values",
            [],
        ),
        "start_line": item["start_line"],
        "end_line": item["end_line"],
        "start_column": item["start_column"],
        "end_column": item["end_column"],
        "parent_function_id": None,
        "class_id": None,
        "class_name": None,
        "qualified_name": None,
    }


def _build_class_symbol(
    item: dict,
    index: int,
) -> dict:
    return {
        "id": (
            f"class:{index}:"
            f"{item['start_line']}:"
            f"{item['start_column']}"
        ),
        "name": item["name"],
        "start_line": item["start_line"],
        "end_line": item["end_line"],
        "start_column": item["start_column"],
        "end_column": item["end_column"],
    }


def _attach_containers(
    functions: list,
    classes: list,
) -> None:
    for function in functions:
        parent_function = _find_parent_function(
            function,
            functions,
        )

        if parent_function is not None:
            function["parent_function_id"] = (
                parent_function["id"]
            )

        parent_class = _find_containing_class(
            function,
            classes,
        )

        if parent_class is not None:
            function["class_id"] = parent_class["id"]
            function["class_name"] = (
                parent_class["name"]
            )


def _assign_qualified_names(
    functions: list,
) -> None:
    by_id = {
        item["id"]: item
        for item in functions
    }

    cache = {}

    def resolve_name(function: dict) -> str:
        function_id = function["id"]

        if function_id in cache:
            return cache[function_id]

        parent_id = function[
            "parent_function_id"
        ]

        if parent_id:
            parent = by_id[parent_id]
            name = (
                f"{resolve_name(parent)}."
                f"{function['name']}"
            )

        elif function["class_name"]:
            name = (
                f"{function['class_name']}."
                f"{function['name']}"
            )

        else:
            name = function["name"]

        cache[function_id] = name
        return name

    for function in functions:
        function["qualified_name"] = (
            resolve_name(function)
        )


def _resolve_call(
    *,
    call_target: str,
    caller: dict,
    functions: list,
    classes: list,
) -> dict:
    target = call_target.strip()

    if not target:
        return {
            "status": RESOLUTION_UNRESOLVED,
            "symbol": None,
        }

    direct_matches = [
        item
        for item in functions
        if item["name"] == target
    ]

    if len(direct_matches) == 1:
        return {
            "status": RESOLUTION_LOCAL,
            "symbol": direct_matches[0],
        }

    if len(direct_matches) > 1:
        return {
            "status": RESOLUTION_AMBIGUOUS,
            "symbol": None,
        }

    member_resolution = (
        _resolve_member_call(
            target=target,
            caller=caller,
            functions=functions,
            classes=classes,
        )
    )

    if member_resolution is not None:
        return member_resolution

    return {
        "status": RESOLUTION_UNRESOLVED,
        "symbol": None,
    }


def _resolve_member_call(
    *,
    target: str,
    caller: dict,
    functions: list,
    classes: list,
) -> dict | None:
    if "." not in target:
        return None

    owner, member = target.rsplit(
        ".",
        1,
    )

    if (
        owner in {"self", "this"}
        and caller["class_id"]
    ):
        matches = [
            item
            for item in functions
            if (
                item["class_id"]
                == caller["class_id"]
                and item["name"] == member
            )
        ]

        return _matches_to_resolution(
            matches
        )

    class_names = {
        item["name"]
        for item in classes
    }

    if owner in class_names:
        matches = [
            item
            for item in functions
            if (
                item["class_name"] == owner
                and item["name"] == member
            )
        ]

        return _matches_to_resolution(
            matches
        )

    return None


def _matches_to_resolution(
    matches: list,
) -> dict:
    if len(matches) == 1:
        return {
            "status": RESOLUTION_LOCAL,
            "symbol": matches[0],
        }

    if len(matches) > 1:
        return {
            "status": RESOLUTION_AMBIGUOUS,
            "symbol": None,
        }

    return {
        "status": RESOLUTION_UNRESOLVED,
        "symbol": None,
    }


def _find_containing_function(
    item: dict,
    functions: list,
) -> dict | None:
    candidates = [
        function
        for function in functions
        if _contains(
            function,
            item,
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=_start_position,
    )


def _find_parent_function(
    function: dict,
    functions: list,
) -> dict | None:
    candidates = [
        candidate
        for candidate in functions
        if (
            candidate["id"]
            != function["id"]
            and _contains(
                candidate,
                function,
            )
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=_start_position,
    )


def _find_containing_class(
    item: dict,
    classes: list,
) -> dict | None:
    candidates = [
        class_item
        for class_item in classes
        if _contains(
            class_item,
            item,
        )
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=_start_position,
    )


def _contains(
    outer: dict,
    inner: dict,
) -> bool:
    outer_start = _start_position(outer)
    outer_end = _end_position(outer)

    inner_start = _start_position(inner)
    inner_end = _end_position(inner)

    return (
        outer_start <= inner_start
        and outer_end >= inner_end
    )


def _start_position(
    item: dict,
) -> tuple:
    return (
        item["start_line"],
        item["start_column"],
    )


def _end_position(
    item: dict,
) -> tuple:
    return (
        item["end_line"],
        item["end_column"],
    )


def _build_unresolved_call(
    call: dict,
    caller: dict | None,
) -> dict:
    return {
        "caller_id": (
            caller["id"]
            if caller
            else None
        ),
        "caller": (
            caller["qualified_name"]
            if caller
            else None
        ),
        "call_target": call["target"],
        "line": call["start_line"],
    }
