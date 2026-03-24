# 🔬 paper-digest

A GitHub Actions workflow that emails you a daily digest of the most relevant
research papers from arXiv and PubMed — personalised to your research interests,
automatically filtered and summarised by AI.

**No server. No always-on computer. Set it up once, forget about it.**

---

## What it looks like

Every morning at 8am, you get an email like this:

> **🔬 Biophysics Digest — 2026-03-24 (6 papers)**
>
> **Active Cahn–Hilliard theory for non-equilibrium phase separation**
> _This paper derives a quantitative field theory for active phase separation..._
> Relevant to your work on Cahn-Hilliard models of biomolecular condensates.
> Methodology: analytical theory + numerical simulation.
>
> ---
> **Condensate-mediated shape transformations of cellular membranes**
> ...

Papers you've already seen are never sent again.

---

## How it works

```
arXiv + PubMed
      ↓
Claude AI scores each abstract for relevance to your topics
      ↓
Top papers summarised with context specific to your research
      ↓
Daily email to your inbox
```

**Cost:** ~$0.04/day (~$1.20/month) using your own Anthropic API key.

---

## Quick start

### 1. Fork this repo

Click **Fork** at the top right of this page.

### 2. Clone and run setup

```bash
git clone https://github.com/YOUR-USERNAME/paper-digest.git
cd paper-digest
python setup.py
```

The setup script will ask you:
- What research topics you care about
- How many papers per digest (default: 8)
- How often to send (daily / every 3 days / weekly)
- Your timezone
- Your recipient email

Then commit and push the changes it makes:

```bash
git add .
git commit -m "Configure my digest"
git push
```

### 3. Set your GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | What to put |
|---|---|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_ADDRESS` | Gmail account that sends the digest |
| `GMAIL_APP_PASSWORD` | [Gmail App Password](https://myaccount.google.com/apppasswords) (not your login password) |
| `RECIPIENT_EMAIL` | Where you want to receive the digest |

### 4. Test it

Go to **Actions** → **Daily Paper Digest** → **Run workflow**

Check your inbox in ~3 minutes. Check spam if it doesn't appear — mark it as
"not spam" so future emails land in your inbox.

That's it. 🎉

---

## Customisation

### Change your topics or frequency later

Just run `setup.py` again:

```bash
python setup.py
git add .
git commit -m "Update topics"
git push
```

### Manual config editing

If you prefer to edit files directly:

- **Topics & max papers** → `config.py`
- **Schedule** → `.github/workflows/daily_digest.yml` (cron expression)

Common cron schedules:
| Schedule | Cron |
|---|---|
| Every day at 8am UTC | `0 8 * * *` |
| Every Monday at 8am UTC | `0 8 * * 1` |
| Every 3 days at 8am UTC | `0 8 */3 * *` |

Use [crontab.guru](https://crontab.guru) to build custom schedules.

---

## Requirements

- A GitHub account (free)
- An Anthropic API account with credit ([$5 minimum](https://console.anthropic.com))
- A Gmail account

No local Python installation required for the workflow itself —
GitHub Actions handles everything. Python is only needed to run `setup.py`.

---

## Cost breakdown

| Step | Model | Cost per day |
|---|---|---|
| Scoring ~50 abstracts | Claude Haiku | ~$0.01 |
| Summarising top papers | Claude Sonnet | ~$0.03 |
| **Total** | | **~$0.04/day** |

You use your own API key, so you pay Anthropic directly.
This project never touches your billing.

---

## Privacy

- Your research topics and email address are stored only in your own GitHub repo
- Papers are fetched from public APIs (arXiv, PubMed) — no login required
- Your API keys are stored in GitHub Secrets and never leave your repo
- The `seen_papers.json` file (committed automatically) contains only paper IDs
  and dates — no personal information

---

## Troubleshooting

**Email went to spam**
Mark it as "not spam" once — Gmail will learn.

**"Credit balance too low" error**
Make sure you have at least $5 in your [Anthropic Console](https://console.anthropic.com)
billing, and that your usage limits are set above $0 under Settings → Limits.

**No papers found today**
You'll receive a short email saying so. Try broadening your topics in `config.py`
or running `setup.py` again.

**Workflow fails on the git push step**
Make sure your workflow has `permissions: contents: write` in the yml file.

---

## Contributing

Found a bug or have a feature idea? Open an issue or a pull request.

This project was built with [Claude Code](https://claude.ai/code).

---

## License

MIT — do whatever you want with it.
