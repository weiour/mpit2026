from __future__ import annotations

import re
from urllib.parse import quote


EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)


def extract_emails(text: str) -> list[str]:
    if not text:
        return []
    return sorted({m.group(0) for m in EMAIL_RE.finditer(text)})


def build_mailto(to: list[str], subject: str, body: str) -> str:
    # mailto uses comma-separated addresses.
    # Spaces and special chars should be percent-encoded.
    if not to:
        return ""
    to_part = ",".join([t.strip() for t in to if t.strip()])
    subj = quote(subject or "", safe="")
    bod = quote(body or "", safe="")
    return f"mailto:{to_part}?subject={subj}&body={bod}"

