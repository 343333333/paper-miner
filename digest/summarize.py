"""Generate HTML digest using Claude Sonnet."""

import os
from datetime import date

import anthropic

from config import MAX_DIGEST_PAPERS, SONNET_MODEL

SYSTEM_PROMPT = """\
You are summarizing today's most relevant biophysics papers for a researcher
with this profile:

They work on theoretical biophysics of cellular organization. Their current
projects involve: (1) phase-field / Cahn-Hilliard models of biomolecular
condensates coupled to moving DNA binding sites, (2) free-energy descriptions
of ER tether binding using Model B dynamics and rapid equilibrium approximations,
(3) reaction-diffusion systems and pattern formation in nonequilibrium biological
contexts. They closely follow the work of Erwin Frey and Nigel Goldenfeld.\
"""


def _format_papers_block(papers: list[dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        lines.append(f"[{i}] Title: {p['title']}")
        lines.append(f"    URL: {p['url']}")
        lines.append(f"    Score: {p['score']} | Topics: {', '.join(p.get('topics', []))}")
        lines.append(f"    Abstract: {p['abstract'][:800]}")
        lines.append("")
    return "\n".join(lines)


def generate_digest(papers: list[dict]) -> str:
    """
    Take top papers (score >= threshold, max MAX_DIGEST_PAPERS) and return HTML digest.
    """
    top = papers[:MAX_DIGEST_PAPERS]
    today = date.today().strftime("%B %d, %Y")
    papers_block = _format_papers_block(top)

    user_msg = f"""\
For each paper below, write:
- A 2–3 sentence plain-language summary of the key result
- One sentence on why it is relevant to this researcher specifically
  (be concrete — name which of their topics it connects to)
- One sentence on methodology (theory / simulation / experiment)

Papers:
{papers_block}

Format the output as clean HTML for an email body.
Use <h2> for "Today's Biophysics Digest — {today}"
Use <h3> for each paper title as a hyperlink to the paper URL
Use <p> for summary paragraphs
Use a subtle <hr> between papers
Keep total length under 900 words.\
"""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return message.content[0].text.strip()
