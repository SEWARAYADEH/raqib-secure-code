import uuid

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    request,
)

from app.api_errors import api_error
from app.analysis_store import (
    AnalysisRecordIntegrityError,
    AnalysisRecordNotFoundError,
)
from app.analysis_service import (
    AnalysisValidationError,
    analyze_source_file,
)
from app.auth import (
    SCOPE_ANALYSIS_CREATE,
    SCOPE_ANALYSIS_READ,
    resolve_analysis_principal,
)
from app.intake import (
    MAX_SOURCE_FILE_BYTES,
    SourceFileValidationError,
)


api = Blueprint(
    "api",
    __name__,
    url_prefix="/api",
)


@api.get("/health")
def health_check():
    return jsonify(
        {
            "status": "ok",
            "service": "step-one-backend",
        }
    )


@api.post("/v1/analysis/source")
def analyze_source():
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
            message="Use multipart/form-data with one file field.",
        )

    files = request.files.getlist("file")

    if len(files) != 1 or not files[0].filename:
        return api_error(
            status_code=400,
            code="INVALID_FILE_COUNT",
            message="Exactly one named source file is required.",
        )

    uploaded = files[0]
    content = uploaded.stream.read(
        MAX_SOURCE_FILE_BYTES + 1
    )

    if len(content) > MAX_SOURCE_FILE_BYTES:
        return api_error(
            status_code=413,
            code="SOURCE_FILE_TOO_LARGE",
            message="The source file exceeds the upload limit.",
        )

    try:
        result = analyze_source_file(
            uploaded.filename,
            content,
        )
    except SourceFileValidationError as exc:
        return api_error(
            status_code=400,
            code="INVALID_SOURCE_FILE",
            message=str(exc),
        )
    except AnalysisValidationError as exc:
        return api_error(
            status_code=422,
            code="UNSUPPORTED_ANALYSIS_INPUT",
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


@api.get("/v1/analyses")
def list_analyses():
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(
            status_code=401,
            code="ANALYSIS_ACCESS_DENIED",
            message="Analysis access is not authorized.",
        )
    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(
            status_code=403,
            code="ANALYSIS_SCOPE_FORBIDDEN",
            message="The principal cannot read analyses.",
        )
    store = current_app.extensions.get("analysis_store")
    if store is None:
        return api_error(
            status_code=503,
            code="ANALYSIS_STORE_DISABLED",
            message="Immutable analysis storage is not enabled.",
        )
    try:
        analyses = store.list_for_owner(principal.subject)
    except AnalysisRecordIntegrityError:
        return api_error(
            status_code=500,
            code="ANALYSIS_INTEGRITY_FAILURE",
            message="An analysis record failed integrity verification.",
        )
    return jsonify({"request_id": g.request_id, "analyses": analyses})


@api.get("/v1/analyses/<analysis_id>")
def get_analysis(analysis_id: str):
    principal = resolve_analysis_principal()

    if principal is None:
        return api_error(
            status_code=401,
            code="ANALYSIS_ACCESS_DENIED",
            message="Analysis access is not authorized.",
        )

    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(
            status_code=403,
            code="ANALYSIS_SCOPE_FORBIDDEN",
            message="The principal cannot read analyses.",
        )

    try:
        normalized_id = str(uuid.UUID(analysis_id))
    except ValueError:
        return api_error(
            status_code=404,
            code="ANALYSIS_NOT_FOUND",
            message="The requested analysis does not exist.",
        )

    store = current_app.extensions.get("analysis_store")

    if store is None:
        return api_error(
            status_code=503,
            code="ANALYSIS_STORE_DISABLED",
            message="Immutable analysis storage is not enabled.",
        )

    try:
        record = store.get(normalized_id)
    except AnalysisRecordNotFoundError:
        return api_error(
            status_code=404,
            code="ANALYSIS_NOT_FOUND",
            message="The requested analysis does not exist.",
        )
    except AnalysisRecordIntegrityError:
        return api_error(
            status_code=500,
            code="ANALYSIS_INTEGRITY_FAILURE",
            message="The analysis record failed integrity verification.",
        )

    if record["owner_subject"] != principal.subject:
        return api_error(
            status_code=403,
            code="ANALYSIS_RECORD_FORBIDDEN",
            message="The analysis belongs to another principal.",
        )

    return jsonify(
        {
            "request_id": g.request_id,
            "record": record,
        }
    )
