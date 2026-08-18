"""
app.py — Platform-Agnostic GPT/Gem/Project Builder Wizard
------------------------------------------------------------
Takes:
  - database_syntax.yaml      (detailed search syntax rules, optional subset)
  - database_directory.md     (full A-Z database list for recommendations + links)
  - guides.csv                (research guides, optional)

...and generates a downloadable package: one set of
instructions + knowledge files that work across ChatGPT Custom GPTs,
Gemini Gems, Claude Projects, and Microsoft Copilot Studio, and Perplexity 
Spaces.

No AI inference happens in this app — it's pure templating/packaging.
"""

import csv
import io
from pathlib import Path

import streamlit as st
import yaml

from generator import build_package
from libguides_import import guess_column, build_directory_from_rows

st.set_page_config(
    page_title="LAIBB - Library (Resource) AI Bridge Builder",
    layout="wide",
)

st.markdown("""
<style>
.app-header h1 { font-size: 4rem; margin: 0; }
.app-header p  { font-size: 1rem; margin: 0; color: #bbb; text-transform: uppercase; }
.step-badge {
    display: inline-block;
    background: yellow;
    color: #000000;
    font-weight: 700;
    border-radius: 20px;
    padding: 0.3rem 0.7rem .1rem;
    font-size: 0.8rem;
    margin-right: 0.5rem;
}
.stMainBlockContainer {padding-top:1rem} 
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <h1>LAIBB - Library (Resource) (gen)AI Bridge Builder</h1>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Generates one package of instructions and knowledge files that helps align mainstream gen AI tools "
    "such as ChatGPT, Claude, Gemini, Copilot Studio, and Perplexity with library research databases."
)

if "config" not in st.session_state:
    st.session_state.config = None
if "guides" not in st.session_state:
    st.session_state.guides = None
if "directory_md" not in st.session_state:
    st.session_state.directory_md = None
if "imported_directory_md" not in st.session_state:
    st.session_state.imported_directory_md = None
if "import_warnings" not in st.session_state:
    st.session_state.import_warnings = []

# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — Organization info
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 1</span> **Organization Info**', unsafe_allow_html=True)

col1, = st.columns(1)
with col1:
    org_name = st.text_input(
        "Library / Institution name",
        placeholder="e.g., W. Frank Steely Library, Northern Kentucky University",
    )
    proxy_prefix = st.text_input(
        "Library proxy prefix (optional)",
        placeholder="e.g., https://your-institution.idm.oclc.org/login?url=",
        help="Prepended to raw database URLs when importing a LibGuides A-Z Database "
             "List export (Step 2) so links carry institutional access. Not needed if "
             "you already have a fully-formed database_directory.md or prefer to generate"
             "a template file in Step 2 that you can manually update later.",
    )

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# STEP 2 — Database directory (recommendations + clickable links)
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 2</span> **Database Directory** '
            '<span style="color:#888;font-weight:400;font-size:0.85rem;">— required for database recommendations & links</span>',
            unsafe_allow_html=True)
st.caption(
    "Upload a markdown file listing your databases with clickable links, "
    "type, and subject tags — used to recommend and link the right "
    "database(s) for a topic. Format: `* [Title](url)` with `**Type:**` and "
    "`**Subjects:**` sub-bullets."
)

dir_source = st.radio(
    "Directory source",
    ["Upload database_directory.md", "Import LibGuides A-Z Databases export (.csv) to generate a database_directory.md",
     "Start with a sample template", "Skip — no directory"],
    horizontal=True,
    label_visibility="collapsed",
)

directory_md = None

if dir_source == "Upload database_directory.md":
    uploaded_md = st.file_uploader("Upload database directory (.md)", type=["md", "markdown"])
    if uploaded_md:
        directory_md = uploaded_md.read().decode("utf-8")

elif dir_source == "Import LibGuides A-Z Databases export (.csv) to generate a database_directory.md":
    st.caption(
        "Upload the CSV export from your LibGuides A-Z Database list (Admin → "
        "A-Z Database List → Export). Column names vary by export — confirm "
        "the mapping below before generating."
    )
    uploaded_csv = st.file_uploader("Upload LibGuides export (.csv)", type=["csv"], key="libguides_csv")

    if uploaded_csv:
        text = uploaded_csv.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        export_rows = list(reader)
        export_columns = reader.fieldnames or []

        st.caption(f"{len(export_rows)} row(s) found. Confirm which column is which:")

        mc1, mc2 = st.columns(2)
        with mc1:
            title_guess = guess_column(export_columns, "title")
            title_col = st.selectbox(
                "Title column", export_columns,
                index=export_columns.index(title_guess) if title_guess in export_columns else 0,
            )
            url_guess = guess_column(export_columns, "url")
            url_col = st.selectbox(
                "URL column", export_columns,
                index=export_columns.index(url_guess) if url_guess in export_columns else 0,
            )
        with mc2:
            type_guess = guess_column(export_columns, "type")
            type_col = st.selectbox(
                "Type column (optional)", ["(none)"] + export_columns,
                index=(export_columns.index(type_guess) + 1) if type_guess in export_columns else 0,
            )
            subjects_guess = guess_column(export_columns, "subjects")
            subjects_col = st.selectbox(
                "Subjects column (optional)", ["(none)"] + export_columns,
                index=(export_columns.index(subjects_guess) + 1) if subjects_guess in export_columns else 0,
            )

        delimiter = st.radio(
            "Multi-value delimiter used within Type/Subjects cells",
            [";", ","], horizontal=True,
        )
        auto_proxy = st.checkbox(
            "Automatically prepend proxy prefix to raw URLs",
            value=bool(proxy_prefix),
            help="Skips URLs that already appear to carry institutional access "
                 "(e.g. already contain your proxy domain or a LibGuides login- link).",
        )
        if auto_proxy and not proxy_prefix:
            st.warning("No proxy prefix set in Step 1 — raw URLs will be left as-is.")

        if st.button("🔄 Convert to database_directory.md"):
            md, import_warnings = build_directory_from_rows(
                rows=export_rows,
                title_col=title_col,
                url_col=url_col,
                type_col=None if type_col == "(none)" else type_col,
                subjects_col=None if subjects_col == "(none)" else subjects_col,
                delimiter=delimiter,
                proxy_prefix=proxy_prefix,
                auto_proxy=auto_proxy,
            )
            st.session_state.imported_directory_md = md
            st.session_state.import_warnings = import_warnings

    if st.session_state.get("imported_directory_md"):
        directory_md = st.session_state.imported_directory_md
        warnings_list = st.session_state.get("import_warnings", [])
        if warnings_list:
            st.warning(f"⚠️ {len(warnings_list)} row(s) flagged for review — "
                       f"generated anyway, but worth a quick check.")
            with st.expander("View flagged rows"):
                st.dataframe(warnings_list, use_container_width=True, height=200)
        else:
            st.success("✅ No issues flagged.")
        st.download_button(
            "⬇️ Download database_directory.md",
            data=directory_md,
            file_name="database_directory.md",
            mime="text/markdown",
        )

elif dir_source == "Start with a sample template":
    sample_dir_path = Path(__file__).parent / "database_directory.md"
    if sample_dir_path.exists():
        directory_md = sample_dir_path.read_text()

if directory_md:
    n_entries = directory_md.count("\n* [")
    st.success(f"✅ Directory ready — approximately {n_entries} database(s)")
    with st.expander("Preview directory (first 2,000 characters)"):
        st.code(directory_md[:2000] + ("..." if len(directory_md) > 2000 else ""), language="markdown")
elif dir_source != "Skip — no directory":
    st.info("No directory loaded yet.")

st.session_state.directory_md = directory_md

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — Search syntax rules (optional, advanced)
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 3</span> **Search Syntax Rules** '
            '<span style="color:#888;font-weight:400;font-size:0.85rem;">— optional, for detailed Boolean search strings</span>',
            unsafe_allow_html=True)
st.caption(
    "Upload `database_syntax.yaml` for the subset of databases you want detailed, "
    "ready-to-paste Boolean search strings for. "
    "Databases not covered here still get recommended from the database directory, "
    "just with plain-language keyword suggestions instead of formal syntax."
)

db_source = st.radio(
    "Syntax rules source",
    ["Upload database_syntax.yaml", "Start from sample template", "Skip — directory only"],
    horizontal=True,
    label_visibility="collapsed",
)

yaml_text = None

if db_source == "Upload database_syntax.yaml":
    uploaded = st.file_uploader("Upload database_syntax.yaml", type=["yaml", "yml"])
    if uploaded:
        yaml_text = uploaded.read().decode("utf-8")
elif db_source == "Start from sample template":
    sample_path = Path(__file__).parent / "database_syntax.yaml"
    if sample_path.exists():
        yaml_text = sample_path.read_text()

parsed_config = {"databases": []}

if yaml_text is not None:
    edited_yaml = st.text_area(
        "Edit syntax rules (YAML)",
        value=yaml_text,
        height=260,
        help="Add/remove databases or adjust syntax_notes directly.",
    )
    try:
        parsed_config = yaml.safe_load(edited_yaml) or {"databases": []}
        n_dbs = len(parsed_config.get("databases", []))
        st.success(f"✅ Parsed successfully — {n_dbs} database(s) with detailed syntax rules")
    except yaml.YAMLError as e:
        st.error(f"YAML parsing error: {e}")
        parsed_config = {"databases": []}
elif db_source == "Skip — directory only":
    st.caption("No syntax rules — recommendations will rely on the directory only.")

st.session_state.config = parsed_config

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# STEP 4 — Research guides
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 4</span> **Research Guides** '
            '<span style="color:#888;font-weight:400;font-size:0.85rem;">— optional</span>',
            unsafe_allow_html=True)
st.caption(
    "Upload a LibGuides guides export (Admin → Guides, any column layout) or a "
    "custom CSV, or start from the sample. Only a title and a URL are needed — "
    "map the columns below; Subject/Type and Description are optional."
)

guides_source = st.radio(
    "Guide source",
    ["Upload guides.csv", "Start from sample template", "Skip — no guides"],
    horizontal=True,
    label_visibility="collapsed",
)

guides_list = []

if guides_source == "Upload guides.csv":
    uploaded_csv = st.file_uploader("Upload guides export (.csv)", type=["csv"])
    if uploaded_csv:
        text = uploaded_csv.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        raw_rows = list(reader)
        raw_columns = reader.fieldnames or []

        st.caption(f"{len(raw_rows)} row(s) found. Confirm which column is which:")
        gc1, gc2 = st.columns(2)
        with gc1:
            g_title_guess = guess_column(raw_columns, "title")
            g_title_col = st.selectbox(
                "Title column", raw_columns,
                index=raw_columns.index(g_title_guess) if g_title_guess in raw_columns else 0,
                key="guides_title_col",
            )
            g_url_guess = guess_column(raw_columns, "url")
            g_url_col = st.selectbox(
                "URL column", raw_columns,
                index=raw_columns.index(g_url_guess) if g_url_guess in raw_columns else 0,
                key="guides_url_col",
            )
        with gc2:
            g_subject_guess = guess_column(raw_columns, "subjects") or guess_column(raw_columns, "type")
            g_subject_col = st.selectbox(
                "Subject/Type column (optional)", ["(none)"] + raw_columns,
                index=(raw_columns.index(g_subject_guess) + 1) if g_subject_guess in raw_columns else 0,
                key="guides_subject_col",
            )
            g_desc_guess = guess_column(raw_columns, "description")
            g_desc_col = st.selectbox(
                "Description column (optional)", ["(none)"] + raw_columns,
                index=(raw_columns.index(g_desc_guess) + 1) if g_desc_guess in raw_columns else 0,
                key="guides_desc_col",
            )

        # LibGuides admin exports usually carry a Status column
        # (Published/Unpublished/Private) — default to Published-only so
        # drafts, internal, and test guides don't leak into the assistant's
        # recommendations, but let the librarian turn it off.
        g_status_guess = guess_column(raw_columns, "status")
        published_only = True
        if g_status_guess:
            published_only = st.checkbox(
                f'Only include rows where "{g_status_guess}" is "Published"',
                value=True,
                key="guides_published_only",
                help="Unchecking includes Unpublished/Private guides too — usually "
                     "not what you want for a public-facing assistant.",
            )

        skipped_status = 0
        skipped_missing = 0
        for row in raw_rows:
            title = (row.get(g_title_col) or "").strip()
            url = (row.get(g_url_col) or "").strip()
            if g_status_guess and published_only and (row.get(g_status_guess) or "").strip().lower() != "published":
                skipped_status += 1
                continue
            if not title or not url:
                skipped_missing += 1
                continue
            guides_list.append({
                "title": title,
                "url": url,
                "subject": (row.get(g_subject_col) or "").strip() if g_subject_col != "(none)" else "",
                "description": (row.get(g_desc_col) or "").strip() if g_desc_col != "(none)" else "",
            })

        if skipped_status:
            st.caption(f"Skipped {skipped_status} non-Published row(s).")
        if skipped_missing:
            st.caption(f"Skipped {skipped_missing} row(s) missing a title or URL.")

elif guides_source == "Start from sample template":
    sample_csv_path = Path(__file__).parent / "guides.csv"
    if sample_csv_path.exists():
        with open(sample_csv_path, newline="", encoding="utf-8-sig") as f:
            sample_reader = csv.DictReader(f)
            sample_rows = list(sample_reader)
            sample_columns = sample_reader.fieldnames or []
        # Map by guessing rather than assuming fixed lowercase headers, since
        # the sample file's exact column names/order/casing may change.
        s_title_col = guess_column(sample_columns, "title")
        s_url_col = guess_column(sample_columns, "url")
        s_subject_col = guess_column(sample_columns, "subjects") or guess_column(sample_columns, "type")
        s_desc_col = guess_column(sample_columns, "description")
        guides_list = [
            {
                "title": (row.get(s_title_col) or "").strip() if s_title_col else "",
                "url": (row.get(s_url_col) or "").strip() if s_url_col else "",
                "subject": (row.get(s_subject_col) or "").strip() if s_subject_col else "",
                "description": (row.get(s_desc_col) or "").strip() if s_desc_col else "",
            }
            for row in sample_rows
        ]

if guides_list:
    st.success(f"✅ {len(guides_list)} research guide(s) loaded")
    with st.expander("Preview guides"):
        st.dataframe(guides_list, use_container_width=True, height=200)
elif guides_source != "Skip — no guides":
    st.info("No guides loaded yet.")

st.session_state.guides = guides_list

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# STEP 5 — Librarian consultation info
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 5</span> **Librarian Consultation Options**', unsafe_allow_html=True)
st.caption("How should the assistant direct users to get in-person help?")

lc1, lc2 = st.columns(2)
with lc1:
    appointments = st.text_input("Appointments", placeholder="Meet with a librarian link: https://...")
with lc2:
    contact_info = st.text_input("General Contact Info", placeholder="General Get Help link: https://...")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# STEP 6 — Generate & download
# ══════════════════════════════════════════════════════════════════════════

st.markdown('<span class="step-badge">STEP 6</span> **Generate Package**', unsafe_allow_html=True)

has_any_content = bool(
    st.session_state.directory_md
    or (st.session_state.config and st.session_state.config.get("databases"))
)
ready = bool(org_name and has_any_content)

if not ready:
    missing = []
    if not org_name:
        missing.append("organization name")
    if not has_any_content:
        missing.append("a database directory and/or syntax rules")
    st.warning(f"Complete these before generating: {', '.join(missing)}")

if st.button("Generate Package", type="primary", disabled=not ready):
    librarian_info = {
        "Appointments": appointments or "(not provided)",
        "General Contact Info": contact_info or "(not provided)",
    }

    zip_bytes, manifest = build_package(
        config=st.session_state.config or {"databases": []},
        guides=st.session_state.guides or [],
        directory_md=st.session_state.directory_md or "",
        org_name=org_name,
        librarian_help_info=librarian_info,
    )

    st.success("Package generated!")

    li = manifest["instructions_length"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Instructions length", f"{li['length']:,} chars")
    c2.metric("Databases w/ syntax rules", manifest["num_databases_with_syntax"])
    c3.metric("Research guides", manifest["num_guides"])

    st.caption(
        f"✅ Within ChatGPT's 8,000 char limit · ✅ Within Claude's 200,000 char limit"
        if li["chatgpt_ok"] else
        f"⚠️ Over ChatGPT's 8,000 char limit by {li['length'] - li['chatgpt_limit']:,} — "
        f"see SETUP_GUIDE.md for how to trim"
    )

    safe_name = "".join(c if c.isalnum() else "_" for c in org_name.lower())[:40]
    st.download_button(
        "⬇️ Download Package (.zip)",
        data=zip_bytes,
        file_name=f"{safe_name}_assistant_package.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )

    st.info(
        "Next steps: unzip the package, open SETUP_GUIDE.md first — it has "
        "setup steps for ChatGPT, Claude, Gemini, Copilot Studio, and Perplexity.",
        icon="📋",
    )
