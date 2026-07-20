# Search Strategy Assistant Builder
**Platform-agnostic — works with ChatGPT, Claude, Gemini, Copilot Studio, and Perplexity**

A Streamlit wizard that turns a library's database directory, search syntax
rules, and research guides into one downloadable package: instructions +
knowledge files that deploy to any major generative AI platform with only
minor per-platform steps (paste here, upload there).

**No AI model runs in this app.** It's a templating/packaging tool — no
Ollama, no server, no GPU, no hosting.

---

## Why "platform-agnostic by default" (Approach B)

Rather than generating separate output per platform (ChatGPT vs. Gemini vs.
Claude), this wizard produces **one canonical content package**. The actual
substance — how to build a search strategy, which databases to recommend,
how to format links — doesn't change based on destination. What differs
between platforms is just where you paste/upload things, which is handled
by the platform-specific sections in the generated `SETUP_GUIDE.md`.

This also solves the character-limit problem architecturally rather than by
warning: database syntax rules live in a knowledge file the AI is instructed
to consult, not inline in the instructions text. That keeps instructions
short (a few thousand characters) regardless of how many databases you
document — comfortably under every major platform's limit.

---

## Three knowledge assets, working together

| File | Purpose | Required? |
|------|---------|-----------|
| `database_directory.md` | Full list of databases with clickable links, type, and subject tags — used to recommend and link the right database(s) for a topic | Recommended |
| `databases.yaml` | Detailed Boolean search syntax rules for a subset of databases (PubMed, CINAHL, etc.) — used to build precise search strings | Optional |
| `guides.csv` | Subject research guides — used for guide recommendations | Optional |

A database can appear in the directory without appearing in the syntax
rules file — in that case the assistant still recommends it and gives the
link, just with plain-language keyword suggestions instead of a formal
Boolean string. This means you don't need to hand-author syntax rules for
every database to get full directory coverage.

---

## A note on Perplexity

Perplexity Spaces work a bit differently from the other platforms: alongside
your uploaded knowledge files, a Space can also search the live web in the
same thread. When testing or using a Perplexity Space built from this
package, keep **"My Files" toggled on** so recommendations stay grounded in
your actual database directory and guides rather than Perplexity surfacing
plausible-sounding databases it found on the open web. The upside of this
platform specifically: a student can get a tailored search strategy from
your knowledge files *and* current scholarly context on their topic in the
same conversation.

---

## No deterministic URL building

This version does not attempt to construct pre-filled search URLs. The
assistant provides a copy/paste-ready search string and a clickable link to
the recommended database (drawn directly from `database_directory.md`,
which already contains institution-proxied links). The user pastes the
search string into the database's own search box after opening it.

---

## Installation & Launch

1. **Install uv** — [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
2. **Launch:**
   - Windows: double-click `launch.bat`
   - Mac/Linux: `chmod +x launch.sh && ./launch.sh` (first time), double-click after

No Ollama needed — this app doesn't run any AI model.

---

## Importing from a LibGuides A-Z export

If you don't already have a `database_directory.md`, you can build one from
a fresh LibGuides A-Z Database export instead of hand-authoring it:

1. In LibGuides, go to **Admin → A-Z Database List → Export** and download the CSV
2. In Step 2 of the wizard, choose **"Import from LibGuides export (.csv)"**
3. Confirm the column mapping — the wizard guesses which uploaded column is
   Title/URL/Type/Subjects, but exports vary, so double-check before converting
4. Choose the delimiter your Type/Subjects cells use to separate multiple
   values (semicolon or comma)
5. Set your **proxy prefix** in Step 1 first — the importer uses it to turn
   raw vendor URLs into working institutional-access links, automatically
   skipping any URL that already appears to carry proxy access
6. Click **Convert** — any rows with missing or suspicious values (e.g. a
   URL slug landing in the Subjects field) are flagged for a quick review,
   but still included in the output rather than silently dropped
7. Download the resulting `database_directory.md` directly, or continue
   straight into package generation

## How to use it

1. **Step 1** — Organization name and (optional) library proxy prefix
2. **Step 2** — Upload `database_directory.md`, import from a LibGuides
   export, or start from the sample
3. **Step 3** — Optionally upload `databases.yaml` for detailed syntax rules
   on specific databases
4. **Step 4** — Optionally upload `guides.csv`
5. **Step 5** — Fill in librarian consultation booking info
6. **Step 6** — Generate and download the `.zip` package

---

## What's in the generated package

| File | Purpose |
|------|---------|
| `instructions.txt` | Paste into the platform's instructions/system prompt field |
| `knowledge_files/database_directory.md` | Upload as a knowledge file |
| `knowledge_files/database_syntax_reference.md` | Upload as a knowledge file (only if syntax rules were provided) |
| `knowledge_files/research_guides.md` | Upload as a knowledge file (only if guides were provided) |
| `SETUP_GUIDE.md` | Step-by-step setup for ChatGPT, Claude, Gemini, Copilot Studio, and Perplexity, plus a testing checklist |

---

## Formatting your own database directory

`database_directory.md` should follow this structure — the AI is instructed
to cite databases using this exact link format, so consistency matters:

```markdown
* [Database Title](https://your-proxied-link-here)
    * **Type:** Articles, Clinical Tools
    * **Subjects:** Nursing & Allied Health
```

Keep the `Type` and `Subjects` tags consistent across entries (e.g. always
"Nursing & Allied Health", not sometimes "Nursing" and sometimes "Allied
Health Sciences") — the AI matches topics against these tags, so
inconsistent vocabulary will reduce match quality.

---

## Files

| File | Purpose | Edit? |
|------|---------|-------|
| `app.py` | Wizard UI | Rarely |
| `generator.py` | Core templating logic | To change output format |
| `database_directory.md` | Sample/starting directory | Yes, or upload your own |
| `databases.yaml` | Sample/starting syntax rules | Yes, or upload your own |
| `guides.csv` | Sample/starting guides list | Yes, or upload your own |

---

## Contact

W. Frank Steely Library · [library@nku.edu](mailto:library@nku.edu)
