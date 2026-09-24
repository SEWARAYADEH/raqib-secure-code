from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


ADVISOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "root_cause_hypotheses",
        "patch_strategy",
        "test_suggestions",
        "uncertainties",
    ],
    "properties": {
        "root_cause_hypotheses": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
        "patch_strategy": {"type": "string"},
        "test_suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5,
        },
        "uncertainties": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5,
        },
    },
}


@dataclass(frozen=True)
class AdvisorConfig:
    enabled: bool
    api_key: str
    model: str
    max_context_characters: int = 6000
    max_output_tokens: int = 1200


class AdvisorUnavailable(RuntimeError):
    pass


def advisor_status(config: AdvisorConfig) -> dict:
    configured = bool(config.api_key and config.model)
    return {
        "provider": "OPENAI_RESPONSES_API",
        "status": "READY" if config.enabled and configured else "DISABLED",
        "reason": (
            None
            if config.enabled and configured
            else "DISABLED_BY_CONFIG"
            if not config.enabled
            else "MISSING_API_KEY_OR_MODEL"
        ),
        "authority": "ADVISORY_ONLY",
        "context_policy": "MINIMUM_NECESSARY_STRUCTURED_EVIDENCE",
        "source_code_included_by_default": False,
        "can_verify_exploitability": False,
        "can_close_findings": False,
    }


def build_minimal_advisor_context(
    *,
    analysis: dict,
    finding_id: str,
    max_characters: int = 6000,
) -> dict:
    finding = next(
        (
            item
            for item in analysis["security_analysis"]["candidates"]
            if item["id"] == finding_id
        ),
        None,
    )
    if finding is None:
        raise ValueError("The requested finding does not exist.")
    context = {
        "schema": "raqeeb-advisor-context-v1",
        "artifact": {
            "sha256": analysis["artifact"]["sha256"],
            "language": analysis["language"]["candidate"],
            "line_count": analysis["artifact"]["line_count"],
        },
        "application": {
            "role": analysis["application_understanding"]["project_role"],
            "frameworks": analysis["application_understanding"]["frameworks"],
            "routes": analysis["application_understanding"]["routes"],
        },
        "finding": finding,
        "constraints": {
            "advisory_only": True,
            "minimal_patch": True,
            "preserve_functionality": True,
            "do_not_claim_verification_or_closure": True,
        },
    }
    encoded = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    if len(encoded) > max_characters:
        context["finding"] = {
            key: finding[key]
            for key in (
                "id",
                "state",
                "source",
                "sink",
                "scope",
                "controls",
                "standards",
            )
        }
        encoded = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    if len(encoded) > max_characters:
        raise ValueError("The minimum advisor context exceeds the configured budget.")
    context["budget"] = {
        "characters": len(encoded),
        "approximate_tokens_upper_bound": (len(encoded) + 3) // 4,
    }
    return context


class CodexAdvisor:
    def __init__(self, config: AdvisorConfig, transport=None) -> None:
        self._config = config
        self._transport = transport or self._send

    def advise(self, context: dict) -> dict:
        status = advisor_status(self._config)
        if status["status"] != "READY":
            raise AdvisorUnavailable(status["reason"])
        payload = {
            "model": self._config.model,
            "store": False,
            "max_output_tokens": self._config.max_output_tokens,
            "instructions": (
                "You are an advisory secure-code reviewer. Use only supplied "
                "evidence. State uncertainties. Propose the smallest patch "
                "strategy and tests. Never claim exploitability, safety, or closure."
            ),
            "input": json.dumps(context, ensure_ascii=False),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "raqeeb_advice",
                    "strict": True,
                    "schema": ADVISOR_SCHEMA,
                }
            },
        }
        result = self._transport(payload)
        advice = json.loads(_output_text(result))
        _validate_advice(advice)
        return {
            "authority": "ADVISORY_ONLY",
            "model": self._config.model,
            "advice": advice,
        }

    def _send(self, payload: dict) -> dict:
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))


def _output_text(response: dict) -> str:
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise AdvisorUnavailable("The provider returned no structured output text.")


def _validate_advice(advice: dict) -> None:
    required = set(ADVISOR_SCHEMA["required"])
    if not isinstance(advice, dict) or set(advice) != required:
        raise AdvisorUnavailable("The advisory response does not match its contract.")
    if not all(isinstance(advice[key], list) for key in required - {"patch_strategy"}):
        raise AdvisorUnavailable("The advisory response contains invalid lists.")
    if not isinstance(advice["patch_strategy"], str):
        raise AdvisorUnavailable("The advisory patch strategy is invalid.")
