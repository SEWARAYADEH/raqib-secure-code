from __future__ import annotations

import hashlib
import hmac
import secrets
import smtplib
import ssl
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(frozen=True)
class ChallengeReceipt:
    challenge_id: str
    expires_in_seconds: int


@dataclass
class _Challenge:
    email: str
    code_digest: str
    expires_at: float
    attempts_remaining: int


class ChallengeRejected(Exception):
    pass


class AddressNotAllowed(ChallengeRejected):
    pass


class DeliveryUnavailable(Exception):
    pass


class EmailChallengeService:
    """Short-lived email verification challenges for one application process.

    The plaintext code exists only while the SMTP message is assembled. Stored
    challenge state contains an HMAC digest and is protected by a process lock.
    A shared durable store is required before running multiple web workers.
    """

    def __init__(
        self,
        *,
        hmac_key: str,
        sender: str,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        allowed_emails: frozenset[str],
        use_ssl: bool = True,
        ttl_seconds: int = 600,
        max_attempts: int = 5,
        minimum_resend_seconds: int = 60,
        clock=time.monotonic,
        mail_sender=None,
    ) -> None:
        if len(hmac_key) < 32:
            raise ValueError("Email verification requires a 32-character HMAC key.")

        self._key = hmac_key.encode("utf-8")
        self._sender = sender
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_username = smtp_username
        self._smtp_password = smtp_password
        self._allowed_emails = allowed_emails
        self._use_ssl = use_ssl
        self._ttl_seconds = ttl_seconds
        self._max_attempts = max_attempts
        self._minimum_resend_seconds = minimum_resend_seconds
        self._clock = clock
        self._mail_sender = mail_sender or self._send_email
        self._challenges: dict[str, _Challenge] = {}
        self._last_issue: dict[str, float] = {}
        self._lock = threading.Lock()

    def issue(self, email: str) -> ChallengeReceipt:
        normalized = normalize_email(email)
        if normalized not in self._allowed_emails:
            raise AddressNotAllowed("Verification is unavailable for this address.")

        now = self._clock()
        with self._lock:
            last_issue = self._last_issue.get(normalized)
            if last_issue is not None and now - last_issue < self._minimum_resend_seconds:
                raise ChallengeRejected("Please wait before requesting another code.")

            self._purge_expired(now)
            challenge_id = secrets.token_urlsafe(32)
            code = f"{secrets.randbelow(1_000_000):06d}"
            challenge = _Challenge(
                email=normalized,
                code_digest=self._digest(challenge_id, code),
                expires_at=now + self._ttl_seconds,
                attempts_remaining=self._max_attempts,
            )
            self._challenges[challenge_id] = challenge
            self._last_issue[normalized] = now

        try:
            self._mail_sender(normalized, code, self._ttl_seconds)
        except Exception as error:
            with self._lock:
                self._challenges.pop(challenge_id, None)
                self._last_issue.pop(normalized, None)
            raise DeliveryUnavailable("The verification email could not be delivered.") from error

        return ChallengeReceipt(challenge_id, self._ttl_seconds)

    def verify(self, challenge_id: str, code: str) -> str:
        if not challenge_id or len(challenge_id) > 128:
            raise ChallengeRejected("The verification challenge is invalid.")
        if len(code) != 6 or not code.isascii() or not code.isdigit():
            raise ChallengeRejected("The verification code is invalid.")

        now = self._clock()
        with self._lock:
            challenge = self._challenges.get(challenge_id)
            if challenge is None or challenge.expires_at <= now:
                self._challenges.pop(challenge_id, None)
                raise ChallengeRejected("The verification challenge is invalid or expired.")

            supplied = self._digest(challenge_id, code)
            if not hmac.compare_digest(supplied, challenge.code_digest):
                challenge.attempts_remaining -= 1
                if challenge.attempts_remaining <= 0:
                    self._challenges.pop(challenge_id, None)
                raise ChallengeRejected("The verification code is invalid or expired.")

            self._challenges.pop(challenge_id, None)
            return challenge.email

    def _digest(self, challenge_id: str, code: str) -> str:
        message = f"{challenge_id}:{code}".encode("utf-8")
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()

    def _purge_expired(self, now: float) -> None:
        expired = [
            challenge_id
            for challenge_id, challenge in self._challenges.items()
            if challenge.expires_at <= now
        ]
        for challenge_id in expired:
            self._challenges.pop(challenge_id, None)

    def _send_email(self, recipient: str, code: str, ttl_seconds: int) -> None:
        if not all(
            (
                self._sender,
                self._smtp_host,
                self._smtp_username,
                self._smtp_password,
            )
        ):
            raise DeliveryUnavailable("SMTP is not configured.")

        message = EmailMessage()
        message["Subject"] = "Raqeeb verification code"
        message["From"] = self._sender
        message["To"] = recipient
        message.set_content(
            "Your Raqeeb verification code is "
            f"{code}. It expires in {ttl_seconds // 60} minutes. "
            "If you did not request it, ignore this message."
        )

        context = ssl.create_default_context()
        if self._use_ssl:
            with smtplib.SMTP_SSL(
                self._smtp_host,
                self._smtp_port,
                timeout=10,
                context=context,
            ) as client:
                client.login(self._smtp_username, self._smtp_password)
                client.send_message(message)
            return

        with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10) as client:
            client.starttls(context=context)
            client.login(self._smtp_username, self._smtp_password)
            client.send_message(message)


def normalize_email(value: str) -> str:
    normalized = value.strip().casefold()
    local, separator, domain = normalized.partition("@")
    if (
        not separator
        or not local
        or not domain
        or len(normalized) > 254
        or any(character.isspace() for character in normalized)
        or "." not in domain
    ):
        raise ChallengeRejected("A valid email address is required.")
    return normalized
