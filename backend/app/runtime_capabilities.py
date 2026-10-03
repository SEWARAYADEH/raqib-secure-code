"""Expose the tested capability of the installed executor, never a config flag."""

from __future__ import annotations

from flask import current_app, has_app_context

from app.runtime_verifier import (
    OciRuntimeConfig,
    OciRuntimeVerifier,
    RuntimeVerifier,
    UnavailableRuntimeVerifier,
)


def get_runtime_verifier() -> RuntimeVerifier:
    engine = _setting("RUNTIME_OCI_ENGINE", "")
    image = _setting("RUNTIME_OCI_IMAGE", "")
    if not engine or not image:
        return UnavailableRuntimeVerifier("OCI_RUNTIME_NOT_CONFIGURED")
    return OciRuntimeVerifier(OciRuntimeConfig(engine=engine, image=image))


def verification_runtime_capability() -> dict:
    return get_runtime_verifier().capability()


def verification_runtime_available() -> bool:
    return bool(verification_runtime_capability()["available"])


def _setting(name: str, default: str) -> str:
    if has_app_context():
        return str(current_app.config.get(name, default)).strip()
    return default
