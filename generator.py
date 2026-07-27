"""
generator.py — Builds platform-agnostic GPT/Gem/Project packages from
database_syntax.yaml + database_directory.md + guides.csv

Approach B: one canonical content package (instructions + knowledge files)
that works across ChatGPT Custom GPTs, Gemini Gems, Claude Projects,
Microsoft Copilot Studio, and Perplexity Spaces with minimal per-platform
adjustment. No AI
inference happens here — this is pure templating.

Three knowledge assets work together:
  - database_directory.md   → full A-Z database list, for recommending and
                                linking the right database(s) to a topic
  - database_syntax.yaml          → detailed search syntax rules for the subset of
                                databases the librarian has hand-documented
  - guides.csv              → subject research guides, for recommendations

No deterministic URL-building. The AI provides a copy/paste-ready search
string and points to the appropriate database link(s) drawn directly from
database_directory.md (which already contains institution-proxied links).
"""

import io
import json
import zipfile
from datetime import date


# ── Instructions Builder (Approach B — platform-agnostic, knowledge-driven) ──

def build_instructions(config: dict, org_name: str, librarian_help_info: dict,
                        has_directory: bool, has_syntax_rules: bool,
                        has_guides: bool) -> str:
    """
    Build the core instructions text. Deliberately short — it describes
    process and points to knowledge files rather than embedding all database
    syntax rules inline. This keeps it comfortably under every major
    platform's instruction length limit without needing to warn or trim.
    """
    lines = []

    lines.append(f"You are an expert academic research librarian assistant for {org_name}.")
    lines.append(
        "Your job is to help students, faculty, and staff develop advanced "
        "search strategies for academic databases, recommend the right "
        "database(s) and research guides for their topic, and connect them "
        "with a librarian for personalized help."
    )
    lines.append("")
    lines.append("KNOWLEDGE FILES AVAILABLE TO YOU:")
    if has_directory:
        lines.append(
            "- database_directory.md — the full list of available research "
            "databases, each with its title, clickable link, content type(s), "
            "and subject area(s)."
        )
    if has_syntax_rules:
        lines.append(
            "- database_syntax_reference.md — detailed Boolean search syntax "
            "rules (field codes, truncation, proximity operators, etc.) for "
            "a subset of databases."
        )
    if has_guides:
        lines.append(
            "- research_guides.md — subject-specific research guides, each "
            "with a title, link, subject tags, and description."
        )
    lines.append("")

    lines.append("PROCESS — follow these steps for every research topic:")
    lines.append("")
    lines.append(
        "1. If the topic is vague, ask 1-2 clarifying questions (e.g. "
        "population, setting, or specific outcomes of interest). Don't "
        "over-ask — proceed with reasonable assumptions if the user seems "
        "to want to move quickly."
    )
    if has_directory:
        lines.append(
            "2. Search database_directory.md for databases whose Subject or "
            "Type tags match the topic. Recommend the 2-4 best-matching "
            "databases. Always cite each one using the exact markdown link "
            "format from the directory: [Database Title](url) — this "
            "renders as a clickable link. Never alter, shorten, or "
            "reconstruct the URL; use it exactly as it appears in the file, "
            "since it is already configured for institutional access."
        )
    if has_syntax_rules:
        lines.append(
            "3. If one of the recommended databases also appears in "
            "database_syntax_reference.md, build a complete, copy-paste-"
            "ready Boolean search string using ONLY that database's "
            "documented syntax rules. Do not mix syntax between databases, "
            "and do not invent field codes or controlled-vocabulary terms "
            "(e.g. MeSH headings) you are not certain exist — default to "
            "free-text/title-abstract searching if unsure."
        )
        lines.append(
            "4. If a recommended database is NOT in database_syntax_reference.md, "
            "still recommend it and provide the link, but instead of a "
            "formal Boolean string, suggest a few plain-language keyword "
            "combinations the user can adapt to that database's own search box."
        )
    lines.append(
        "5. Combine controlled vocabulary terms with free-text synonyms "
        "using OR to improve recall. Group synonyms with OR, combine "
        "concept groups with AND, and use parentheses to nest."
    )
    lines.append(
        "6. After each search string, give a 2-3 sentence plain-language "
        "explanation of the concept groupings, and suggest 1-2 additional "
        "terms the user might consider."
    )
    if has_guides:
        lines.append(
            "7. Check research_guides.md and recommend 1-3 relevant guides "
            "with a one-sentence reason each, citing the exact title and "
            "link from the file. Only recommend guides that actually appear "
            "there — never invent a title or URL. If nothing is a strong "
            "match, say so."
        )
    lines.append("")

    lines.append("CONNECTING USERS WITH A LIBRARIAN:")
    lines.append(
        "After providing search strategies (or if the user seems stuck, "
        "frustrated, or wants more help than a search string can offer), "
        "mention they can meet with a librarian for personalized research help:"
    )
    for role, info in librarian_help_info.items():
        lines.append(f"  - {role}: {info}")
    lines.append(
        "Mention this naturally, once per conversation — don't repeat it on "
        "every message."
    )
    lines.append("")

    lines.append("TONE & STYLE:")
    lines.append(
        "Be warm, encouraging, and clear — like a helpful librarian, not a "
        "search engine. Avoid jargon without explanation. Keep responses "
        "focused: database recommendations with clickable links, a search "
        "string when applicable, a short explanation, guide recommendations, "
        "and (when relevant) the librarian appointment note. Don't pad "
        "responses with unnecessary preamble."
    )

    return "\n".join(lines)


def measure_instructions(instructions: str) -> dict:
    """
    Report length against known platform limits, for informational display
    in the wizard. No platform-specific trimming happens automatically —
    Approach B is designed to stay comfortably under all of these by keeping
    syntax rules out of the instructions text entirely.
    """
    length = len(instructions)
    return {
        "length": length,
        "chatgpt_limit": 8000,
        "chatgpt_ok": length <= 8000,
        "claude_limit": 200_000,
        "claude_ok": length <= 200_000,
    }


# ── Knowledge File Builders ───────────────────────────────────────────────────

def build_guides_knowledge_file(guides: list[dict]) -> str:
    """Format guides.csv rows as a clean markdown knowledge file."""
    lines = [f"# Research Guides Index", f"_Generated {date.today().isoformat()}_", ""]
    lines.append(
        "This file lists available subject research guides. Only recommend "
        "guides that appear below — never invent a title or URL."
    )
    lines.append("")

    for g in guides:
        lines.append(f"## {g['title']}")
        lines.append(f"- **Subjects:** {g['subject']}")
        lines.append(f"- **URL:** {g['url']}")
        lines.append(f"- **Description:** {g['description']}")
        lines.append("")

    return "\n".join(lines)


def build_database_reference_file(config: dict) -> str:
    """
    Markdown reference of detailed search syntax rules for the subset of
    databases the librarian has hand-documented in database_syntax.yaml.
    """
    lines = [f"# Database Search Syntax Reference", f"_Generated {date.today().isoformat()}_", ""]
    lines.append(
        "This file documents detailed Boolean search syntax for a subset of "
        "databases. For the full list of available databases (used to "
        "recommend and link the right database for a topic), see "
        "database_directory.md."
    )
    lines.append("")

    for db in config.get("databases", []):
        lines.append(f"## {db['name']}")
        if db.get("search_url"):
            lines.append(f"- **Reference link:** {db['search_url']}")
        lines.append("")
        lines.append("**Syntax rules:**")
        lines.append("```")
        lines.append(db.get("syntax_notes", "").strip())
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def prepare_directory_file(directory_md: str) -> str:
    """
    Pass the uploaded database directory markdown through with minimal
    modification. The directory is already in the exact format the AI
    should cite from ([Title](url) with Type/Subjects), so this is close
    to a no-op — reserved for light normalization if needed later.
    """
    return directory_md.strip() + "\n"


# ── Package Assembly ──────────────────────────────────────────────────────────

def build_package(config: dict, guides: list[dict], directory_md: str,
                   org_name: str, librarian_help_info: dict) -> tuple[bytes, dict]:
    """
    Assemble the full downloadable package as an in-memory zip.
    Returns (zip_bytes, metadata_dict) for display in the wizard UI.
    """
    has_directory = bool(directory_md and directory_md.strip())
    has_syntax_rules = bool(config.get("databases"))
    has_guides = bool(guides)

    instructions = build_instructions(
        config, org_name, librarian_help_info,
        has_directory=has_directory,
        has_syntax_rules=has_syntax_rules,
        has_guides=has_guides,
    )
    length_info = measure_instructions(instructions)

    setup_guide = build_setup_guide(
        org_name, length_info,
        has_directory=has_directory,
        has_syntax_rules=has_syntax_rules,
        has_guides=has_guides,
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("instructions.txt", instructions)
        if has_directory:
            zf.writestr("knowledge_files/database_directory.md",
                        prepare_directory_file(directory_md))
        if has_syntax_rules:
            zf.writestr("knowledge_files/database_syntax_reference.md",
                        build_database_reference_file(config))
        if has_guides:
            zf.writestr("knowledge_files/research_guides.md",
                        build_guides_knowledge_file(guides))
        zf.writestr("SETUP_GUIDE.md", setup_guide)

    buf.seek(0)
    manifest = {
        "instructions_length": length_info,
        "num_databases_with_syntax": len(config.get("databases", [])),
        "num_guides": len(guides),
        "has_directory": has_directory,
    }
    return buf.getvalue(), manifest


def build_setup_guide(org_name: str, length_info: dict, has_directory: bool,
                       has_syntax_rules: bool, has_guides: bool) -> str:
    knowledge_list = []
    if has_directory:
        knowledge_list.append("`knowledge_files/database_directory.md`")
    if has_syntax_rules:
        knowledge_list.append("`knowledge_files/database_syntax_reference.md`")
    if has_guides:
        knowledge_list.append("`knowledge_files/research_guides.md`")
    knowledge_str = ", ".join(knowledge_list) if knowledge_list else "(none included)"

    return f"""# Setup Guide — {org_name} Search Strategy Assistant

This package is **platform-agnostic**: the same `instructions.txt` and
knowledge files work across ChatGPT, Claude, Gemini, Microsoft Copilot
Studio, and Perplexity with only minor differences in where you paste/upload them.

## What's in this package

- **instructions.txt** — Paste into the platform's instructions/system
  prompt field. ({length_info['length']:,} characters — comfortably under
  ChatGPT's 8,000 character limit and Claude's much larger limit.)
- **Knowledge files** — Upload these to the platform's knowledge/file
  section: {knowledge_str}
- **This file** — Setup steps per platform, plus a testing checklist

## Why instructions are short

Rather than embedding every database's search syntax directly in the
instructions field (which quickly exceeds length limits), syntax rules and
the database directory live in separate knowledge files. The AI is
instructed to consult them. This keeps instructions portable across
platforms with very different length limits, and means updating a database's
syntax rules or adding a new one never requires touching instructions.txt.

---

## ChatGPT (Custom GPT)

1. Go to **chatgpt.com/gpts/editor** (requires ChatGPT Plus, Team, or Enterprise)
2. Click **Create a GPT** → switch to the **Configure** tab
3. Name it (e.g. "{org_name} Research Assistant") and add a short description
4. Paste `instructions.txt` into the **Instructions** field
5. Under **Knowledge**, upload each file listed above
6. Under **Capabilities**, leave Web Browsing and Code Interpreter OFF unless
   you have a specific reason — they can cause the model to deviate from
   your database syntax rules
7. Under **Sharing**, choose visibility — "Only people with a link" is a
   good starting point for a pilot

## Claude (Project)

1. Create a new **Project** in Claude
2. Open **Project knowledge** and upload each knowledge file listed above
3. Open **Project instructions** (or "Custom instructions") and paste the
   contents of `instructions.txt`
4. Claude's project instructions have a much higher length limit than
   ChatGPT, so there's headroom if you want to expand the instructions later

## Gemini (Gem)

1. Open **Gemini** → **Gems** → **Create a Gem**
2. Paste `instructions.txt` into the Gem's instructions field
3. Under **Knowledge**, upload each knowledge file listed above
4. Save and test — Gemini Gems have fewer configuration options than
   Custom GPTs, so behavior may vary slightly; test the same topics you'd
   test on other platforms

## Microsoft Copilot Studio (Agent)

1. In Copilot Studio, create a new **Agent**
2. Paste `instructions.txt` into the agent's core **Instructions**
3. Add each knowledge file as a **Knowledge source** (file upload), or —
   since this is a Microsoft-native platform — consider pointing the guides
   and directory sources at a live **SharePoint list** instead of a static
   file, so they stay current automatically
4. Publish to Teams or embed on a library web page; NKU SSO applies
   automatically since users are already authenticated in the tenant

## Perplexity (Space)

1. Open **Spaces** → **Create a Space**
2. Name it (e.g. "{org_name} Research Assistant") and paste `instructions.txt`
   into the **Custom Instructions** field
3. Under **Files**, upload each knowledge file listed above
4. When searching within the Space, keep **"My Files"** toggled on so
   answers stay grounded in your uploaded knowledge files rather than
   general web results. Perplexity can also search the web alongside your
   files in the same thread if you want both — useful for pairing a
   tailored search strategy with current scholarly context on the topic
5. Free accounts support up to 25 files per Space, Pro up to 50–100 — this
   package's file count is well within either limit

---

## Testing checklist (do this on whichever platform you deploy to)

- [ ] Ask about 2-3 real research topics and confirm the databases
      recommended are genuinely relevant (spot-check against a librarian's
      judgment)
- [ ] Confirm each recommended database is cited as a clickable link, and
      the link matches exactly what's in `database_directory.md`
- [ ] For databases with documented syntax rules, confirm the search string
      uses correct field codes (compare against a manual search)
- [ ] For databases without documented syntax rules, confirm the assistant
      still recommends them with a link, using plain-language keywords
      rather than inventing formal syntax
- [ ] Guide recommendations only cite guides that actually exist in the file
- [ ] Librarian appointment info appears once per conversation, not on
      every message

## Updating content later

To update guides, the database directory, or syntax rules, regenerate this
package from the wizard with your updated files, then replace the
Instructions and/or Knowledge files on your chosen platform. Changes take
effect immediately for all users — no redeployment needed.
"""
