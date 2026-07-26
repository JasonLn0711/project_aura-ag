from __future__ import annotations

import re


CREDENTIAL_PATTERNS = (
    re.compile(
        r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----.*?"
        r"-----END (?:[A-Z ]+)?PRIVATE KEY-----",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:"
        r"\bsk-[A-Za-z0-9_-]{12,}\b"
        r"|\bgh[pousr]_[A-Za-z0-9]{20,}\b"
        r"|\bAKIA[A-Z0-9]{16}\b"
        r"|\bxox[baprs]-[A-Za-z0-9-]{12,}\b"
        r"|\bhf_[A-Za-z0-9]{20,}\b"
        r"|\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        r"|\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"
        r"|\b(?:authorization|access[_-]?token|refresh[_-]?token|api[_-]?key|"
        r"password|client[_-]?secret|aws[_-]?secret[_-]?access[_-]?key|token)"
        r"\s*[:=]\s*(?:bearer\s+)?[A-Za-z0-9._~+/=-]{8,}"
        r")",
        re.IGNORECASE,
    ),
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
TAIWAN_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+886[- ]?|0)9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)"
)
TAIWAN_NATIONAL_ID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[A-Z][12]\d{8}(?!\d)"
)


def redact_sensitive_text(value: str) -> str:
    text = str(value)
    for pattern in CREDENTIAL_PATTERNS:
        text = pattern.sub("[REDACTED_CREDENTIAL]", text)
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    text = TAIWAN_PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    return TAIWAN_NATIONAL_ID_PATTERN.sub("[REDACTED_ID]", text)
