"""Expose the capability of the installed executor, not a config flag."""

from app.runtime_verifier import UnavailableRuntimeVerifier


def verification_runtime_available() -> bool:
    return UnavailableRuntimeVerifier().capability()["available"]
