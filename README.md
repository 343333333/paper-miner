# Daily Biophysics Paper Digest

## What This Does

A GitHub Actions workflow that runs every day at 8:00 AM (your local time).
It searches arXiv and PubMed for recent papers matching your research interests,
uses Claude AI to score and summarize the most relevant ones,
and sends you a clean digest email.

No server. No always-on computer. Just push to GitHub and forget about it.

---

## Research Topics to Cover

The researcher works at the intersection of **theoretical biophysics** and
**cell biology**, using phase-field models, free-energy frameworks, and
reaction-diffusion theory to study spatiotemporal organization in cells.

Search for papers related to ANY of the following clusters:

### Cluster A — Biological systems (experimental + theory)
1. **ER transport & secretory pathway** — COPII vesicle budding, ER export sites,
   ER-to-Golgi trafficking, cargo sorting, membrane curvature
2. **ER-mitochondria contact sites** — MAM (mitochondria-associated membranes),
   organelle tethering proteins (MFN2, VDAC, IP3R), lipid transfer,
   calcium signaling at contact sites, organelle contact site biology broadly
3. **Biomolecular condensates** — phase separation in cells, transcriptional
   condensates, protein-DNA interactions driving condensate formation,
   coarsening dynamics, liquid-liquid phase separation (LLPS)

### Cluster B — Theoretical frameworks & methods
4. **Phase-field and free-energy models** — Cahn-Hilliard equation, Model B
   dynamics, Flory-Huggins theory, chemical potential formulations,
   field-theoretic approaches to soft matter and cell biology
5. **Reaction-diffusion systems** — Turing instability, pattern formation,
   activator-inhibitor models, spatial stochastic dynamics, morphogenesis,
   biochemical oscillations (e.g. Min protein system)
6. **Nonequilibrium and active systems** — active matter, driven systems,
   Onsager reciprocal relations, entropy production, fluctuation theorems,
   nonequilibrium steady states, active noise

### Cluster C — Theoretical physicists whose work to prioritize
- **Erwin Frey** (LMU Munich) — active matter, reaction-diffusion, Min proteins,
  stochastic dynamics
- **Nigel Goldenfeld** (UC San Diego) — nonequilibrium physics, pattern formation,
  renormalization group in biology
- Papers citing or building on their group's recent work

### Scoring priority
- Score 10: directly relevant to Cluster A AND uses methods from Cluster B
- Score 8–9: strongly relevant to one cluster, touching another
- Score 6–7: relevant to one cluster only
- Score < 6: discard
- **Always boost by +2** if a paper involves moving or dynamic boundaries
  (e.g. moving DNA, dynamic membranes) coupled to concentration fields —
  this is the researcher's most specific current interest

---

## Tech Stack

| Component | Choice | Reason |
|---|---|---|
| Scheduling | GitHub Actions (cron) | Free, runs without your computer |
| arXiv search | arXiv API (free, no key needed) | Best for physics/biophysics preprints |
| PubMed search | NCBI E-utilities API (free) | Best for cell biology / molecular biology |
| AI scoring & summary | Claude API (`claude-haiku-4-5`) | Fast and cheap for batch processing |
| Email delivery | Gmail SMTP via Python | Simple, reliable |

Why Haiku and not Sonnet? Each daily run may process 30–60 abstracts.
Haiku costs ~10× less per token and is fast enough for abstract scoring.
Sonnet is only called for the final summary of top papers (max 5 per day).

---

## Project Structure

```
paper-digest/
├── .github/
│   └── workflows/
│       └── daily_digest.yml   # GitHub Actions schedule + job definition
├── digest/
│   ├── search.py              # Fetch papers from arXiv and PubMed
│   ├── score.py               # Claude Haiku scores each abstract (0–10)
│   ├── summarize.py           # Claude Sonnet writes digest for top papers
│   ├── deduplicator.py        # Read/write seen_papers.json to skip already-sent papers
│   └── email_sender.py        # Sends the final email via Gmail SMTP
├── data/
│   └── seen_papers.json       # Persistent record of all previously sent paper IDs
├── main.py                    # Entry point: orchestrates the full pipeline
├── config.py                  # Topics, date range, scoring thresholds
├── requirements.txt
└── README.md
```

---

## Implementation — Phase by Phase

### Phase 1 — Paper Search (`digest/search.py`)

Fetch papers published in the **last 24 hours** from both sources.

**arXiv search:**
- Use the arXiv API: `http://export.arxiv.org/api/query`
- Search categories: `q-bio.SC`, `q-bio.CB`, `physics.bio-ph`, `cond-mat.soft`
- Query terms: combine topic keywords with OR logic
- Return fields: `id`, `title`, `authors`, `abstract`, `published`, `arxiv_url`
- Max results per query: 50

**PubMed search:**
- Use NCBI E-utilities: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- Two-step: `esearch` to get IDs, then `efetch` to get abstracts
- Search query: build from topic keywords joined with OR
- Filter: last 1 day (`reldate=1`)
- Max results: 50
- Return same fields as arXiv

**Deduplication:**
- Some papers appear on both arXiv and PubMed
- Deduplicate by normalized title (lowercase, strip punctuation)

**Done when:** Running `python main.py --search-only` prints a list of
raw paper titles with their source (arXiv / PubMed).

---

### Phase 1b — Deduplication (`digest/deduplicator.py`)

Prevent the same paper from appearing in the digest more than once,
even across multiple days.

**`data/seen_papers.json` format:**
```json
{
  "papers": [
    {
      "id": "arxiv:2403.12345",
      "title": "Some paper title",
      "sent_date": "2026-03-22"
    }
  ]
}
```

**Logic:**
- On startup, load `seen_papers.json` (create empty file if it doesn't exist)
- After fetching papers from search, filter out any whose `id` already appears
  in `seen_papers.json`
- After a successful email send, append all newly sent paper IDs to
  `seen_papers.json` and commit the file back to the repo
- Paper IDs: use `arxiv:{arxiv_id}` for arXiv papers, `pubmed:{pmid}` for PubMed

**Committing back to the repo from GitHub Actions:**

Add these steps to `daily_digest.yml` after the main run:
```yaml
- name: Save seen papers
  run: |
    git config user.name "paper-digest-bot"
    git config user.email "bot@github-actions"
    git add data/seen_papers.json
    git diff --staged --quiet || git commit -m "Update seen papers [skip ci]"
    git push
```

The `[skip ci]` tag prevents this commit from triggering another workflow run.

**Done when:** Running the full pipeline twice in a row sends different papers
the second time (or "no new papers" if all are already seen).

---

### Phase 2 — Scoring (`digest/score.py`)

Use `claude-haiku-4-5` to score each paper's relevance.

**For each paper, send this prompt:**

```
You are assisting a theoretical biophysics researcher. Score this paper's
relevance to their work. They study:

BIOLOGICAL SYSTEMS:
- ER transport, COPII vesicle budding, ER-to-Golgi trafficking
- ER-mitochondria contact sites (MAM, tethering, calcium signaling)
- Biomolecular condensates, liquid-liquid phase separation, protein-DNA
  interactions driving condensate formation

THEORETICAL METHODS they use and follow:
- Phase-field models (Cahn-Hilliard, Model B, Flory-Huggins free energy)
- Reaction-diffusion systems (Turing patterns, activator-inhibitor models)
- Nonequilibrium and active systems, Onsager formalism

KEY RESEARCHERS whose work is always relevant: Erwin Frey, Nigel Goldenfeld.

Paper title: {title}
Abstract: {abstract}

Return a JSON object with:
- "score": integer 0–10
- "topics": list of matched topic keywords (e.g. ["condensate", "Cahn-Hilliard"])
- "reason": one sentence explaining the score
- "dynamic_boundary": true if the paper involves concentration fields coupled
  to moving or dynamic boundaries/membranes/DNA (add 2 bonus points to score)

Return only valid JSON. No markdown.
```

**Scoring rules:**
- Score ≥ 7: include in digest
- Score < 7: discard silently
- If topics list has 2+ entries: add 2 bonus points (cap at 10)
- Process papers in parallel batches of 10 to stay within rate limits

**Done when:** Running `python main.py --score-only` prints scored papers
with their scores and matched topics.

---

### Phase 3 — Summarize (`digest/summarize.py`)

Take the top papers (score ≥ 7, max 8 papers) and write the digest.

Use `claude-sonnet-4-20250514` for this step only.

**Prompt:**

```
You are summarizing today's most relevant biophysics papers for a researcher
with this profile:

They work on theoretical biophysics of cellular organization. Their current
projects involve: (1) phase-field / Cahn-Hilliard models of biomolecular
condensates coupled to moving DNA binding sites, (2) free-energy descriptions
of ER tether binding using Model B dynamics and rapid equilibrium approximations,
(3) reaction-diffusion systems and pattern formation in nonequilibrium biological
contexts. They closely follow the work of Erwin Frey and Nigel Goldenfeld.

For each paper below, write:
- A 2–3 sentence plain-language summary of the key result
- One sentence on why it is relevant to this researcher specifically
  (be concrete — name which of their topics it connects to)
- One sentence on methodology (theory / simulation / experiment)

Papers:
{list of title + abstract for each top paper}

Format the output as clean HTML for an email body.
Use <h2> for "Today's Biophysics Digest — {date}"
Use <h3> for each paper title as a hyperlink to the paper URL
Use <p> for summary paragraphs
Use a subtle <hr> between papers
Keep total length under 900 words.
```

**Done when:** Running `python main.py --summarize-only` prints the HTML digest
to the console.

---

### Phase 4 — Email (`digest/email_sender.py`)

Send the HTML digest via Gmail SMTP.

**Configuration (from environment variables):**
```
GMAIL_ADDRESS   = sender Gmail address
GMAIL_APP_PASSWORD = Gmail App Password (not the account password)
RECIPIENT_EMAIL = your email address
```

**Email format:**
- Subject: `🔬 Biophysics Digest — {date} ({n} papers)`
- Body: the HTML from Phase 3
- If 0 papers scored ≥ 7: send a short plain-text email saying
  "No highly relevant papers found today."
- If the API or SMTP fails: do not crash silently — print the full error
  so GitHub Actions logs capture it

**Done when:** A test email arrives in your inbox with correct formatting.

---

### Phase 5 — GitHub Actions Workflow

**File: `.github/workflows/daily_digest.yml`**

```yaml
name: Daily Paper Digest

on:
  schedule:
    - cron: '0 0 * * *'  # 00:00 UTC = 08:00 Beijing time
  workflow_dispatch:      # Allow manual trigger from GitHub UI

jobs:
  digest:
    runs-on: ubuntu-latest
    permissions:
      contents: write     # Needed to commit seen_papers.json back to repo
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
      - name: Save seen papers
        run: |
          git config user.name "paper-digest-bot"
          git config user.email "bot@github-actions"
          git add data/seen_papers.json
          git diff --staged --quiet || git commit -m "Update seen papers [skip ci]"
          git push
```

**Done when:** Manual trigger from GitHub Actions tab runs successfully
and email arrives.

---

## GitHub Secrets to Set

Go to your GitHub repo → Settings → Secrets and variables → Actions → New secret.

Add these four:

| Secret name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key from console.anthropic.com |
| `GMAIL_ADDRESS` | The Gmail account that sends the email |
| `GMAIL_APP_PASSWORD` | A Gmail App Password (see note below) |
| `RECIPIENT_EMAIL` | The email address that receives the digest |

**Gmail App Password:** Go to myaccount.google.com → Security → 2-Step Verification → App passwords. Create one called "Paper Digest". Use this 16-character password, not your regular Gmail password.

---

## Cost Estimate

| Item | Daily cost |
|---|---|
| Haiku scoring ~50 abstracts | ~$0.01 |
| Sonnet summarizing top 8 papers | ~$0.03 |
| **Total per day** | **~$0.04** |
| **Total per month** | **~$1.20** |

---

## Instructions for Claude Code

Read this README and implement it phase by phase, starting with Phase 1.

Confirm each phase works before proceeding:
- Phase 1 ✓ when: raw paper list prints to console
- Phase 1b ✓ when: running pipeline twice skips already-seen papers
- Phase 2 ✓ when: scored list prints with scores, topics, and dynamic_boundary flag
- Phase 3 ✓ when: HTML digest prints to console with researcher-specific relevance notes
- Phase 4 ✓ when: test email arrives in inbox
- Phase 5 ✓ when: GitHub Actions manual trigger succeeds and seen_papers.json is committed

For Phase 4 testing, use `--test` flag to send email with dummy content
without calling the APIs.

Ask before making any decisions not covered in this README.
