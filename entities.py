"""Deterministic entity extraction for Robin V1.2.

The extractor is intentionally local and dependency-free. It uses conservative
regular expressions plus standard-library validation/canonicalization.
"""

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


ONION_URL_RE = re.compile(
    r"(?i)\bhttps?://(?:[a-z2-7]{16}|[a-z2-7]{56})\.onion"
    r"(?::\d{1,5})?(?:/[^\s<>'\"]*)?"
)
EMAIL_RE = re.compile(
    r"(?i)(?<![\w.+-])"
    r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}(?![\w.-])"
)
DOMAIN_RE = re.compile(
    r"(?i)(?<![\w.-])"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}\b"
)
IPV4_CANDIDATE_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
IPV6_CANDIDATE_RE = re.compile(
    r"(?<![0-9A-Fa-f:])([0-9A-Fa-f:]*:[0-9A-Fa-f:]+)(?![0-9A-Fa-f:])"
)
MD5_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])")
SHA1_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
SHA256_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")
CVE_RE = re.compile(r"(?i)\bCVE-\d{4}-\d{4,7}\b")
HANDLE_RE = re.compile(r"(?<![\w@])@[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}")

_URL_TRAILING_PUNCTUATION = ".,;:!?)]}\"'"


def _stable_unique(values):
    """Return exact-value unique strings in deterministic lexical order."""
    return sorted(set(values), key=lambda value: (value.lower(), value))


def _normalize_onion_url(raw_url):
    candidate = raw_url.rstrip(_URL_TRAILING_PUNCTUATION)
    try:
        parsed = urlsplit(candidate)
        hostname = (parsed.hostname or "").lower()
        if not hostname.endswith(".onion"):
            return None

        # Accessing parsed.port validates the port syntax/range.
        port = parsed.port
        netloc = hostname if port is None else f"{hostname}:{port}"
        return urlunsplit((parsed.scheme.lower(), netloc, parsed.path, parsed.query, ""))
    except (TypeError, ValueError):
        return None


def _extract_ip_addresses(text, version):
    pattern = IPV4_CANDIDATE_RE if version == 4 else IPV6_CANDIDATE_RE
    values = []
    for raw in pattern.findall(text):
        if version == 6 and raw.count(":") < 2:
            continue
        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if address.version == version:
            values.append(str(address))
    return _stable_unique(values)


def extract_entities(text):
    """Extract deterministic, grouped entities from page text.

    Args:
        text: normalized page text. Non-string values are converted to strings;
            ``None`` is treated as an empty string.

    Returns:
        Dict[str, list[str]] with stable keys and deterministic value ordering.
    """
    if text is None:
        text = ""
    elif not isinstance(text, str):
        text = str(text)

    onion_urls = []
    for raw_url in ONION_URL_RE.findall(text):
        normalized = _normalize_onion_url(raw_url)
        if normalized:
            onion_urls.append(normalized)

    emails = [match.lower() for match in EMAIL_RE.findall(text)]

    domains = []
    for match in DOMAIN_RE.findall(text):
        domain = match.lower().rstrip(".")
        if not domain.endswith(".onion"):
            domains.append(domain)

    return {
        "onion_urls": _stable_unique(onion_urls),
        "emails": _stable_unique(emails),
        "domains": _stable_unique(domains),
        "ipv4": _extract_ip_addresses(text, 4),
        "ipv6": _extract_ip_addresses(text, 6),
        "md5": _stable_unique(match.lower() for match in MD5_RE.findall(text)),
        "sha1": _stable_unique(match.lower() for match in SHA1_RE.findall(text)),
        "sha256": _stable_unique(match.lower() for match in SHA256_RE.findall(text)),
        "cves": _stable_unique(match.upper() for match in CVE_RE.findall(text)),
        "handles": _stable_unique(
            handle.rstrip(".-") for handle in HANDLE_RE.findall(text) if handle.rstrip(".-")
        ),
    }
