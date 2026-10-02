import hashlib
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
from app.archive_intake import (
    MAX_ARCHIVE_BYTES,
    SOURCE_EXTENSIONS,
)
from app.intake import (
    MAX_SOURCE_FILE_BYTES,
    SourceFileValidationError,
)
from app.security_packs.registry import pack_coverage
from app.repair_proposals import RepairNotAvailable, propose_repair
from app.runtime_capabilities import verification_runtime_available


api = Blueprint(
    "api",
    __name__,
    url_prefix="/api",
)

MAX_REPAIR_FILE_BYTES = 256 * 1024


@api.get("/health")
def health_check():
    return jsonify(
        {
            "status": "ok",
            "service": "step-one-backend",
        }
    )


@api.get("/v1/examples")
def public_examples():
    """Expose only synthetic evaluation summaries, never uploaded user code."""
    return jsonify({"examples": current_app.extensions["example_catalog"].list_examples()})


@api.get("/v1/analysis/options")
def analysis_options():
    return jsonify(
        {
            "scopes": [
                {
                    "id": "file",
                    "label": "Code file",
                    "accept": ".py,.js,.jsx",
                    "max_bytes": MAX_SOURCE_FILE_BYTES,
                },
                {
                    "id": "project",
                    "label": "ZIP project",
                    "accept": ".zip",
                    "max_bytes": MAX_ARCHIVE_BYTES,
                },
            ],
            "supported_languages": [
                "Python",
                "JavaScript",
                "JavaScript JSX",
            ],
            "project_source_extensions": sorted(SOURCE_EXTENSIONS),
            "security_packs": pack_coverage(),
            "workflow_stages": [
                {"id": "UPLOAD", "status": "AVAILABLE"},
                {"id": "UNDERSTAND", "status": "PARTIAL"},
                {"id": "TRACE", "status": "PARTIAL"},
                {"id": "DETECT", "status": "PARTIAL"},
                {"id": "VERIFY", "status": "NOT_AVAILABLE"},
                {"id": "FIX", "status": "NOT_AVAILABLE"},
                {"id": "TEST", "status": "NOT_AVAILABLE"},
                {"id": "RE_VERIFY", "status": "NOT_AVAILABLE"},
                {"id": "EVIDENCE", "status": "NOT_AVAILABLE"},
            ],
            "safety": {
                "uploaded_code_execution": False,
                "original_overwritten": False,
                "archive_nested_archives_allowed": False,
                "archive_symlinks_allowed": False,
                "analysis_claim_policy": "EVIDENCE_GATED",
                "closure_requires": [
                    "FUNCTIONAL_TEST",
                    "REPLAY",
                    "RE_SCAN",
                    "RE_TRACE",
                    "CLOSURE_EVIDENCE",
                ],
            },
        }
    )


@api.get("/v1/configuration/status")
def configuration_status():
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(
            status_code=401,
            code="ANALYSIS_ACCESS_DENIED",
            message="Configuration status is not authorized.",
        )
    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(
            status_code=403,
            code="ANALYSIS_SCOPE_FORBIDDEN",
            message="The principal cannot read configuration status.",
        )
    config = current_app.config
    return jsonify({
        "ai": {
            "provider": "OpenAI Responses API",
            "enabled": bool(config["CODEX_ADVISOR_ENABLED"]),
            "key_configured": bool(config["OPENAI_API_KEY"]),
            "model_configured": bool(config["OPENAI_MODEL"]),
            "model": config["OPENAI_MODEL"] or None,
            "context_limit_characters": config["CODEX_CONTEXT_MAX_CHARACTERS"],
            "decision_authority": "ADVISORY_ONLY",
        },
        "analysis": {
            "supported_languages": ["Python", "JavaScript", "JavaScript JSX"],
            "osv_advisory_lookup_enabled": bool(
                config["OSV_ADVISORY_LOOKUP_ENABLED"]
            ),
            "uploaded_code_execution": False,
            "isolation_runtime_available": verification_runtime_available(),
        },
        "storage": {
            "enabled": bool(config["ANALYSIS_STORE_ENABLED"]),
            "integrity": "HMAC-SHA256" if config["ANALYSIS_STORE_ENABLED"]
            else "NOT_ENABLED",
            "analysis_records": "OWNER_SCOPED_APPEND_ONLY",
            "uploaded_source_retention": "TEMPORARY_WORKSPACE_ONLY",
            "original_overwritten": False,
        },
        "email": {
            "enabled": bool(config["EMAIL_VERIFICATION_ENABLED"]),
            "credentials_present": bool(
                config["SMTP_HOST"] and config["SMTP_USERNAME"]
                and config["SMTP_PASSWORD"] and config["SMTP_SENDER"]
            ),
            "delivery_verified": False,
        },
    })


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


@api.post("/v1/analyses/<analysis_id>/repair-proposal")
def create_repair_proposal(analysis_id: str):
    """Re-upload the original; return an unverified patch without storing source."""
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(status_code=401, code="ANALYSIS_ACCESS_DENIED",
                         message="Analysis access is not authorized.")
    if not principal.permits(SCOPE_ANALYSIS_CREATE):
        return api_error(status_code=403, code="ANALYSIS_SCOPE_FORBIDDEN",
                         message="The principal cannot create a repair proposal.")
    try:
        normalized_id = str(uuid.UUID(analysis_id))
    except ValueError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    store = current_app.extensions.get("analysis_store")
    if store is None:
        return api_error(status_code=503, code="ANALYSIS_STORE_DISABLED",
                         message="Saved analysis is required.")
    try:
        record = store.get(normalized_id)
    except AnalysisRecordNotFoundError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    except AnalysisRecordIntegrityError:
        return api_error(status_code=500, code="ANALYSIS_INTEGRITY_FAILURE",
                         message="The analysis record failed integrity verification.")
    if record["owner_subject"] != principal.subject:
        return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                         message="The analysis belongs to another principal.")
    if record["result"].get("analysis", {}).get("scope") != "FILE":
        return api_error(status_code=422, code="REPAIR_SCOPE_UNSUPPORTED",
                         message="Only a single saved Python file is supported.")
    if request.mimetype != "multipart/form-data":
        return api_error(status_code=415, code="UNSUPPORTED_MEDIA_TYPE",
                         message="Use multipart/form-data.")
    uploaded = request.files.getlist("file")
    finding_id = request.form.get("finding_id", "")
    if len(uploaded) != 1 or not uploaded[0].filename or not finding_id:
        return api_error(status_code=400, code="INVALID_REPAIR_INPUT",
                         message="One original file and a finding ID are required.")
    content = uploaded[0].stream.read(MAX_REPAIR_FILE_BYTES + 1)
    if len(content) > MAX_REPAIR_FILE_BYTES:
        return api_error(status_code=413, code="SOURCE_FILE_TOO_LARGE",
                         message="The repair proposal limit is 256 KB.")
    if (uploaded[0].filename != record["result"]["artifact"]["filename"]
            or hashlib.sha256(content).hexdigest() != record["artifact_sha256"]):
        return api_error(status_code=409, code="ORIGINAL_FILE_MISMATCH",
                         message="Re-upload the exact file used for this analysis.")
    if not any(item["id"] == finding_id for item in
               record["result"]["security_analysis"]["candidates"]):
        return api_error(status_code=404, code="FINDING_NOT_FOUND",
                         message="The finding is not in this saved analysis.")
    try:
        proposal = propose_repair(uploaded[0].filename, content, finding_id)
    except (RepairNotAvailable, SourceFileValidationError, AnalysisValidationError) as exc:
        return api_error(status_code=422, code="REPAIR_NOT_AVAILABLE",
                         message=str(exc))
    saved_evidence = store.create_repair_evidence(
        analysis_id=normalized_id, owner_subject=principal.subject,
        proposal=proposal,
    )
    return jsonify({"request_id": g.request_id, "proposal": proposal,
                    "saved_evidence": {key: saved_evidence[key] for key in
                                       ("evidence_id", "created_at", "integrity")}})


@api.get("/v1/analyses/<analysis_id>/repair-evidence/<finding_id>")
def latest_repair_evidence(analysis_id: str, finding_id: str):
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(status_code=401, code="ANALYSIS_ACCESS_DENIED",
                         message="Analysis access is not authorized.")
    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(status_code=403, code="ANALYSIS_SCOPE_FORBIDDEN",
                         message="The principal cannot read repair evidence.")
    try:
        normalized_id = str(uuid.UUID(analysis_id))
    except ValueError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    store = current_app.extensions.get("analysis_store")
    if store is None:
        return api_error(status_code=503, code="ANALYSIS_STORE_DISABLED",
                         message="Saved analysis is required.")
    try:
        saved = store.latest_repair_evidence(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id,
        )
    except AnalysisRecordNotFoundError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    except PermissionError:
        return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                         message="The analysis belongs to another principal.")
    except AnalysisRecordIntegrityError:
        return api_error(status_code=500, code="ANALYSIS_INTEGRITY_FAILURE",
                         message="The repair evidence failed integrity verification.")
    return jsonify({"request_id": g.request_id, "saved_evidence": saved})
