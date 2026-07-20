"""
libguides_import.py — Converts a LibGuides A-Z Database export (CSV) into the
clean database_directory.md format the builder wizard expects.

Handles the realities of raw exports:
  - Column names vary (Name vs Title, Subject vs Subjects, etc.) — resolved
    via a guess-then-confirm mapping step in the UI, not assumed here.
  - Type/Subject fields are often multi-value in a single cell, delimited
    by semicolons or commas — split and cleaned here.
  - URLs are often the raw vendor URL, not yet wrapped with the library's
    proxy — optionally prefixed here if not already proxied.
  - Some rows have missing or suspicious values (e.g. a URL slug landing in
    the Subjects cell) — flagged for the librarian to review, not silently
    dropped or guessed at.
"""

import re


# ── Column name guessing ──────────────────────────────────────────────────────

_COLUMN_CANDIDATES = {
    "title":       ["title", "name", "database name", "database", "az title"],
    "url":         ["url", "link", "database url", "proxied url", "resource url"],
    "type":        ["type", "resource type", "types", "content type", "format"],
    "subjects":    ["subject", "subjects", "subject(s)", "subject area", "subject areas"],
    "description": ["description", "desc", "notes", "summary"],
}


def guess_column(columns: list[str], field: str) -> str | None:
    """Best-effort guess of which uploaded column maps to a given field."""
    candidates = _COLUMN_CANDIDATES.get(field, [])
    lower_map = {c.lower().strip(): c for c in columns}

    # Exact match first
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]

    # Substring match as fallback
    for col in columns:
        col_lower = col.lower().strip()
        for cand in candidates:
            if cand in col_lower or col_lower in cand:
                return col

    return None


# ── Value cleaning ────────────────────────────────────────────────────────────

def split_multivalue(cell: str, delimiter: str = ";") -> list[str]:
    """Split a multi-value cell into clean, deduplicated, trimmed values."""
    if not cell or not cell.strip():
        return []
    # Support the chosen delimiter, but also tolerate the other common one
    parts = re.split(r"[;,]" if delimiter in (";", ",") else re.escape(delimiter), cell)
    seen = []
    for p in parts:
        v = p.strip().strip(".").strip()
        if v and v not in seen:
            seen.append(v)
    return seen


_SUSPICIOUS_PATTERNS = [
    re.compile(r"^login-[\w-]+$", re.IGNORECASE),   # a URL slug landed in the wrong field
    re.compile(r"^https?://", re.IGNORECASE),        # a URL landed in the wrong field
    re.compile(r"^(yes|no|true|false)$", re.IGNORECASE),  # a boolean flag landed in the wrong field
]


def looks_suspicious(value: str) -> bool:
    """Flag values that look like they belong in a different column."""
    if not value:
        return False
    return any(p.match(value.strip()) for p in _SUSPICIOUS_PATTERNS)


# ── URL normalization ──────────────────────────────────────────────────────────

def looks_already_proxied(url: str, proxy_prefix: str) -> bool:
    """
    Heuristic: does this URL already carry institutional access, such that
    prepending the proxy prefix again would be wrong or redundant?
    """
    if not url:
        return False
    url_lower = url.lower()
    if proxy_prefix and proxy_prefix.lower().rstrip("/") in url_lower:
        return True
    # Common patterns for "already handled" links across OCLC/EZproxy/LibGuides setups
    markers = ["idm.oclc.org", "/login?url=", "libguides.com/login-", "ezproxy"]
    return any(m in url_lower for m in markers)


def normalize_url(raw_url: str, proxy_prefix: str, auto_proxy: bool) -> str:
    """Apply the proxy prefix to a raw URL, unless it's already proxied or auto_proxy is off."""
    raw_url = (raw_url or "").strip()
    if not raw_url:
        return raw_url
    if not auto_proxy or not proxy_prefix:
        return raw_url
    if looks_already_proxied(raw_url, proxy_prefix):
        return raw_url
    return proxy_prefix.rstrip() + raw_url


# ── Main conversion ────────────────────────────────────────────────────────────

def build_directory_from_rows(
    rows: list[dict],
    title_col: str,
    url_col: str,
    type_col: str | None,
    subjects_col: str | None,
    delimiter: str,
    proxy_prefix: str,
    auto_proxy: bool,
) -> tuple[str, list[dict]]:
    """
    Convert parsed CSV rows into database_directory.md markdown.

    Returns (markdown_text, warnings) where warnings is a list of
    {row_index, title, issue} dicts for the UI to display for review —
    nothing is silently dropped, everything still gets written to the
    output, but flagged rows are surfaced for a quick manual check.
    """
    lines = [
        "---",
        "title: Database Directory",
        "description: Imported from LibGuides A-Z export.",
        "---",
        "# Database Directory",
    ]
    warnings = []

    for i, row in enumerate(rows):
        title = (row.get(title_col) or "").strip()
        raw_url = (row.get(url_col) or "").strip()

        if not title:
            warnings.append({"row_index": i, "title": "(missing)", "issue": "No title — row skipped"})
            continue
        if not raw_url:
            warnings.append({"row_index": i, "title": title, "issue": "No URL — row skipped"})
            continue

        url = normalize_url(raw_url, proxy_prefix, auto_proxy)

        types = split_multivalue(row.get(type_col, ""), delimiter) if type_col else []
        subjects = split_multivalue(row.get(subjects_col, ""), delimiter) if subjects_col else []

        for t in types:
            if looks_suspicious(t):
                warnings.append({"row_index": i, "title": title,
                                  "issue": f'Suspicious Type value: "{t}" — check source column mapping'})
        for s in subjects:
            if looks_suspicious(s):
                warnings.append({"row_index": i, "title": title,
                                  "issue": f'Suspicious Subject value: "{s}" — check source column mapping'})
        if not types:
            warnings.append({"row_index": i, "title": title, "issue": "No Type value"})
        if not subjects:
            warnings.append({"row_index": i, "title": title, "issue": "No Subjects value"})

        lines.append(f"* [{title}]({url})")
        lines.append(f"    * **Type:** {', '.join(types) if types else '*(not listed)*'}")
        lines.append(f"    * **Subjects:** {', '.join(subjects) if subjects else '*(not listed)*'}")

    return "\n".join(lines) + "\n", warnings
