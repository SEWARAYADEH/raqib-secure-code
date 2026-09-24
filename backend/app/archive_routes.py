from __future__ import annotations

import uuid
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request

from app.api_errors import api_error
from app.archive_intake import (
    MAX_ARCHIVE_BYTES,
    SourceArchiveValidationError,
)
from app.archive_service import analyze_source_archive
from app.auth import (
    SCOPE_ANALYSIS_CREATE,
    resolve_analysis_principal,
)


archive_api = Blueprint(
    "archive_api",
    __name__,
    url_prefix="/api/v1/analysis",
)


@archive_api.post("/archive")
def analyze_archive():
    principal = resolve_analysis_principal()

    if principal is None:
        return api_error(
            status_code=401,
            code="ANALYSIS_ACCESS_DENIED",
            message="Analysis access is not authorized.",
        )

    if not principal.permits(SCOPE_ANALYSIS_CREATE):
        return api_error(
            status_code=403,
            code="ANALYSIS_SCOPE_FORBIDDEN",
            message="The principal cannot create analyses.",
        )

    if request.mimetype != "multipart/form-data":
        return api_error(
            status_code=415,
            code="UNSUPPORTED_MEDIA_TYPE",
            message="Use multipart/form-data with one archive field.",
        )

    files = request.files.getlist("archive")

    if len(files) != 1 or not files[0].filename:
        return api_error(
            status_code=400,
            code="INVALID_ARCHIVE_COUNT",
            message="Exactly one named ZIP archive is required.",
        )

    uploaded = files[0]
    content = uploaded.stream.read(MAX_ARCHIVE_BYTES + 1)

    if len(content) > MAX_ARCHIVE_BYTES:
        return api_error(
            status_code=413,
            code="ARCHIVE_TOO_LARGE",
            message="The ZIP archive exceeds the upload limit.",
        )

    workspace_root = current_app.config.get(
        "WORKSPACE_ROOT"
    ) or str(Path(current_app.instance_path) / "workspaces")

    try:
        result = analyze_source_archive(
            filename=uploaded.filename,
            content=content,
            workspace_root=workspace_root,
        )
    except SourceArchiveValidationError as exc:
        return api_error(
            status_code=400,
            code="INVALID_SOURCE_ARCHIVE",
            message=str(exc),
        )

    analysis_id = str(uuid.uuid4())
    store = current_app.extensions.get("analysis_store")
    record = (
        store.create(
            analysis_id=analysis_id,
            owner_subject=principal.subject,
            result=result,
        )
        if store is not None
        else {
            "analysis_id": analysis_id,
            "persisted": False,
        }
    )

    return jsonify(
        {
            "request_id": g.request_id,
            "principal": {
                "subject": principal.subject,
                "role": principal.role,
            },
            "record": record,
            "result": result,
        }
    )
