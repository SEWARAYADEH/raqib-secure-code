import hashlib
import io
import json
import urllib.error
import uuid

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    request,
    send_file,
)
from werkzeug.utils import secure_filename

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
from app.codex_advisor import (
    AdvisorConfig,
    AdvisorUnavailable,
    CodexAdvisor,
    build_minimal_advisor_context,
)
from app.archive_intake import (
    MAX_ARCHIVE_BYTES,
    SOURCE_EXTENSIONS,
)
from app.intake import (
    MAX_SOURCE_FILE_BYTES,
    SourceFileValidationError,
)
from app.finding_lifecycle import build_finding_lifecycle
from app.security_packs.registry import pack_coverage
from app.repair_proposals import RepairNotAvailable, propose_repair
from app.runtime_capabilities import (
    get_runtime_verifier,
    verification_runtime_available,
    verification_runtime_capability,
)


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
            "security_packs": pack_coverage(
                runtime_available=verification_runtime_available()
            ),
            "workflow_stages": [
                {"id": "UPLOAD", "status": "AVAILABLE"},
                {"id": "UNDERSTAND", "status": "PARTIAL"},
                {"id": "TRACE", "status": "PARTIAL"},
                {"id": "DETECT", "status": "PARTIAL"},
                {"id": "VERIFY", "status": (
                    "PARTIAL" if verification_runtime_available() else "NOT_AVAILABLE"
                ), "scope": "REVIEWED_SINGLE_FILE_SQL_COMMAND_REPLAY"},
                {"id": "FIX", "status": "PARTIAL", "scope": "SUPPORTED_PYTHON_PROPOSAL"},
                {"id": "TEST", "status": "PARTIAL", "scope": "PINNED_TRUSTED_FIXTURE"},
                {"id": "RE_VERIFY", "status": "PARTIAL", "scope": "STATIC_RE_SCAN_AND_RE_TRACE"},
                {"id": "EVIDENCE", "status": "PARTIAL",
                 "scope": "SIGNED_REPAIR_RUNTIME_AND_CLOSURE_RECORDS"},
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
            "isolation_runtime": verification_runtime_capability(),
        },
        "storage": {
            "enabled": bool(config["ANALYSIS_STORE_ENABLED"]),
            "integrity": "HMAC-SHA256" if config["ANALYSIS_STORE_ENABLED"]
            else "NOT_ENABLED",
            "analysis_records": "OWNER_SCOPED_APPEND_ONLY",
            "uploaded_source_retention": "TEMPORARY_WORKSPACE_ONLY",
            "patched_artifact_retention": (
                "OWNER_SCOPED_AES_GCM" if config["ANALYSIS_STORE_ENABLED"]
                else "NOT_ENABLED"
            ),
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


@api.post("/v1/analyses/<analysis_id>/findings/<finding_id>/advice")
def advise_on_finding(analysis_id: str, finding_id: str):
    """Send only bounded saved evidence to the optional advisory provider."""
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(status_code=401, code="ANALYSIS_ACCESS_DENIED",
                         message="Analysis access is not authorized.")
    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(status_code=403, code="ANALYSIS_SCOPE_FORBIDDEN",
                         message="The principal cannot read this finding.")
    if request.mimetype != "application/json":
        return api_error(status_code=415, code="UNSUPPORTED_MEDIA_TYPE",
                         message="Use application/json.")
    if request.content_length is not None and request.content_length > 1024:
        return api_error(status_code=413, code="ADVISOR_INPUT_TOO_LARGE",
                         message="Only a file path selector is accepted.")
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or set(body) != {"file_path"}:
        return api_error(status_code=400, code="INVALID_ADVISOR_INPUT",
                         message="A file_path selector is required.")
    file_path = body["file_path"]
    if not isinstance(file_path, str) or not 0 < len(file_path) <= 512 or len(finding_id) > 128:
        return api_error(status_code=400, code="INVALID_ADVISOR_INPUT",
                         message="The finding selector is invalid.")
    try:
        normalized_id = str(uuid.UUID(analysis_id))
    except ValueError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The requested analysis does not exist.")
    store = current_app.extensions.get("analysis_store")
    if store is None:
        return api_error(status_code=503, code="ANALYSIS_STORE_DISABLED",
                         message="Saved analysis is required.")
    try:
        record = store.get(normalized_id)
    except AnalysisRecordNotFoundError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The requested analysis does not exist.")
    except AnalysisRecordIntegrityError:
        return api_error(status_code=500, code="ANALYSIS_INTEGRITY_FAILURE",
                         message="The analysis record failed integrity verification.")
    if record["owner_subject"] != principal.subject:
        return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                         message="The analysis belongs to another principal.")
    files = record["result"].get("files") or [record["result"]]
    matches = [file for file in files
               if (file.get("artifact", {}).get("relative_path")
                   or file.get("artifact", {}).get("filename")) == file_path
               and any(candidate.get("id") == finding_id for candidate in
                       file.get("security_analysis", {}).get("candidates", []))]
    if len(matches) != 1:
        return api_error(status_code=404, code="FINDING_NOT_FOUND",
                         message="The finding is not unique in the selected file.")
    config = current_app.config
    advisor_config = AdvisorConfig(
        enabled=bool(config["CODEX_ADVISOR_ENABLED"]),
        api_key=config["OPENAI_API_KEY"],
        model=config["OPENAI_MODEL"],
        max_context_characters=config["CODEX_CONTEXT_MAX_CHARACTERS"],
    )
    try:
        context = build_minimal_advisor_context(
            analysis=matches[0], finding_id=finding_id,
            max_characters=advisor_config.max_context_characters,
        )
    except ValueError:
        return api_error(status_code=422, code="ADVISOR_CONTEXT_UNAVAILABLE",
                         message="The saved evidence exceeds the advisor context budget.")
    try:
        advice = CodexAdvisor(advisor_config).advise(context)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            return api_error(status_code=503, code="ADVISOR_QUOTA_UNAVAILABLE",
                             message="The configured AI project has no available API quota or credits.")
        return api_error(status_code=503, code="ADVISOR_UNAVAILABLE",
                         message="The advisory provider did not return valid advice.")
    except (AdvisorUnavailable, urllib.error.URLError, TimeoutError, OSError,
            ValueError):
        return api_error(status_code=503, code="ADVISOR_UNAVAILABLE",
                         message="The advisory provider did not return valid advice.")
    return jsonify({"request_id": g.request_id, "analysis_id": normalized_id,
                    "finding_id": finding_id, "file_path": file_path,
                    "context_budget": context["budget"], "result": advice})


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


@api.post("/v1/analyses/<analysis_id>/findings/<finding_id>/verify-repair")
def verify_repair(analysis_id: str, finding_id: str):
    """Replay a saved patch only inside the reviewed, capability-tested OCI runtime."""
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(status_code=401, code="ANALYSIS_ACCESS_DENIED",
                         message="Analysis access is not authorized.")
    if not principal.permits(SCOPE_ANALYSIS_CREATE):
        return api_error(status_code=403, code="ANALYSIS_SCOPE_FORBIDDEN",
                         message="The principal cannot run verification.")
    try:
        normalized_id = str(uuid.UUID(analysis_id))
    except ValueError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    store = current_app.extensions.get("analysis_store")
    if store is None:
        return api_error(status_code=503, code="ANALYSIS_STORE_DISABLED",
                         message="Saved analysis is required.")
    if request.mimetype != "multipart/form-data":
        return api_error(status_code=415, code="UNSUPPORTED_MEDIA_TYPE",
                         message="Use multipart/form-data.")
    uploaded = request.files.getlist("file")
    if len(uploaded) != 1 or not uploaded[0].filename:
        return api_error(status_code=400, code="INVALID_VERIFICATION_INPUT",
                         message="The exact original file is required.")
    content = uploaded[0].stream.read(MAX_REPAIR_FILE_BYTES + 1)
    if len(content) > MAX_REPAIR_FILE_BYTES:
        return api_error(status_code=413, code="SOURCE_FILE_TOO_LARGE",
                         message="The verification limit is 256 KB.")
    try:
        record = store.get(normalized_id)
        if record["owner_subject"] != principal.subject:
            return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                             message="The analysis belongs to another principal.")
        result = record["result"]
        if result.get("analysis", {}).get("scope") != "FILE":
            return api_error(status_code=422, code="VERIFICATION_SCOPE_UNSUPPORTED",
                             message="Isolated verification currently supports one Python file.")
        if (uploaded[0].filename != result["artifact"]["filename"]
                or hashlib.sha256(content).hexdigest() != record["artifact_sha256"]):
            return api_error(status_code=409, code="ORIGINAL_FILE_MISMATCH",
                             message="Re-upload the exact immutable analysis input.")
        matches = [item for item in result["security_analysis"]["candidates"]
                   if item["id"] == finding_id]
        if len(matches) != 1:
            return api_error(status_code=404, code="FINDING_NOT_FOUND",
                             message="The finding is missing or ambiguous.")
        artifact = store.get_patched_artifact(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id,
        )
        if artifact is None:
            return api_error(status_code=409, code="PATCHED_ARTIFACT_REQUIRED",
                             message="Create and save a supported patch first.")
        verifier = get_runtime_verifier()
        capability = verifier.capability()
        if not capability["available"]:
            return api_error(status_code=503, code="ISOLATION_RUNTIME_UNAVAILABLE",
                             message=capability["reason"])
        runtime_evidence = verifier.verify_repair(
            filename=uploaded[0].filename, original=content,
            patched=artifact[0], finding=matches[0],
        )
        saved_verification = store.create_verification_evidence(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id, repair_evidence_id=artifact[1]["evidence_id"],
            evidence=runtime_evidence,
        )
        lifecycle = build_finding_lifecycle(
            finding=matches[0], analysis=result, saved_repair=artifact[1],
            saved_verification=saved_verification,
            runtime_capability=capability,
        )
        closure_record = None
        if lifecycle["closure"]["verified_closed"]:
            closure_record = store.create_closure_record(
                analysis_id=normalized_id, owner_subject=principal.subject,
                finding_id=finding_id,
                verification_evidence_id=saved_verification["evidence_id"],
                closure=lifecycle["closure"],
            )
            lifecycle = build_finding_lifecycle(
                finding=matches[0], analysis=result, saved_repair=artifact[1],
                saved_verification=saved_verification, closure_record=closure_record,
                runtime_capability=capability,
            )
    except AnalysisRecordNotFoundError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    except PermissionError:
        return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                         message="The analysis belongs to another principal.")
    except AnalysisRecordIntegrityError:
        return api_error(status_code=500, code="ANALYSIS_INTEGRITY_FAILURE",
                         message="Saved lifecycle evidence failed integrity verification.")
    except (RuntimeError, ValueError) as exc:
        return api_error(status_code=422, code="VERIFICATION_NOT_AVAILABLE",
                         message=str(exc))
    return jsonify({
        "request_id": g.request_id,
        "verification": {key: saved_verification[key] for key in
                         ("evidence_id", "created_at", "integrity", "evidence")},
        "closure_record": closure_record,
        "lifecycle": lifecycle,
    })


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


@api.get("/v1/analyses/<analysis_id>/findings/<finding_id>/lifecycle")
def finding_lifecycle(analysis_id: str, finding_id: str):
    """One owner-scoped lifecycle contract and its authenticated downloads."""
    principal = resolve_analysis_principal()
    if principal is None:
        return api_error(status_code=401, code="ANALYSIS_ACCESS_DENIED",
                         message="Analysis access is not authorized.")
    if not principal.permits(SCOPE_ANALYSIS_READ):
        return api_error(status_code=403, code="ANALYSIS_SCOPE_FORBIDDEN",
                         message="The principal cannot read this finding.")
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
        if record["owner_subject"] != principal.subject:
            return api_error(status_code=403, code="ANALYSIS_RECORD_FORBIDDEN",
                             message="The analysis belongs to another principal.")
        file_path = request.args.get("file", "")
        if len(file_path) > 512:
            return api_error(status_code=400, code="INVALID_FINDING_SELECTOR",
                             message="The file selector is too long.")
        files = record["result"].get("files") or [record["result"]]
        if file_path == "@project" and record["result"].get("files"):
            matches = [
                (record["result"], candidate)
                for candidate in record["result"].get("security_analysis", {}).get("candidates", [])
                if candidate.get("id") == finding_id
            ]
        else:
            matches = [(file, candidate) for file in files
                       if not file_path or (file.get("artifact", {}).get("relative_path")
                                            or file.get("artifact", {}).get("filename")) == file_path
                       for candidate in file.get("security_analysis", {}).get("candidates", [])
                       if candidate.get("id") == finding_id]
        if len(matches) != 1:
            return api_error(status_code=404, code="FINDING_NOT_FOUND",
                             message="The finding is missing or ambiguous.")
        file, finding = matches[0]
        saved = store.latest_repair_evidence(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id,
        ) if record["result"].get("analysis", {}).get("scope") == "FILE" else None
        saved_verification = store.latest_verification_evidence(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id,
        ) if saved else None
        closure_record = store.latest_closure_record(
            analysis_id=normalized_id, owner_subject=principal.subject,
            finding_id=finding_id,
        ) if saved_verification else None
        lifecycle = build_finding_lifecycle(
            finding=finding, analysis=file, saved_repair=saved,
            saved_verification=saved_verification, closure_record=closure_record,
            runtime_capability=verification_runtime_capability(),
        )
        download = request.args.get("download")
        if download == "patched":
            artifact = store.get_patched_artifact(
                analysis_id=normalized_id, owner_subject=principal.subject,
                finding_id=finding_id,
            )
            if artifact is None:
                return api_error(status_code=404, code="PATCHED_ARTIFACT_NOT_FOUND",
                                 message="No saved patched artifact is available.")
            filename = secure_filename(file["artifact"]["filename"])
            stem = filename.rsplit(".", 1)[0] or "patched"
            response = send_file(io.BytesIO(artifact[0]), mimetype="text/x-python",
                                 as_attachment=True, download_name=f"{stem}.proposed.py")
        elif download == "report":
            report = {"analysis_id": normalized_id,
                      "created_at": record["created_at"],
                      "artifact": file.get("artifact"),
                      "finding": finding,
                      "lifecycle": lifecycle}
            response = send_file(io.BytesIO(json.dumps(report, ensure_ascii=False,
                                                      indent=2).encode("utf-8")),
                                 mimetype="application/json", as_attachment=True,
                                 download_name=f"raqib-security-report-{normalized_id}.json")
        elif download is None:
            return jsonify({"request_id": g.request_id, "analysis_id": normalized_id,
                            "file_path": (
                                "@project" if file_path == "@project"
                                else file.get("artifact", {}).get("relative_path")
                                or file.get("artifact", {}).get("filename")
                            ),
                            "lifecycle": lifecycle})
        else:
            return api_error(status_code=400, code="INVALID_DOWNLOAD",
                             message="The requested download is not available.")
    except AnalysisRecordNotFoundError:
        return api_error(status_code=404, code="ANALYSIS_NOT_FOUND",
                         message="The analysis does not exist.")
    except AnalysisRecordIntegrityError:
        return api_error(status_code=500, code="ANALYSIS_INTEGRITY_FAILURE",
                         message="The saved evidence failed integrity verification.")
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
