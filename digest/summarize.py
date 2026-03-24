"""Generate HTML digest using Claude Sonnet."""

import os
from datetime import date

import anthropic

from config import MAX_DIGEST_PAPERS, SONNET_MODEL

SYSTEM_PROMPT = """\
You are summarizing today's most relevant computational chemistry papers for a
researcher with this profile:

They work on computational and theoretical chemistry. Their current interests
involve: (1) many-body potentials, many-body expansion, and permutationally
invariant polynomials, (2) machine learning force fields including MACE,
universal interatomic potentials, and CCSD(T)-level ML potentials, (3)
GPU-accelerated simulation and Density Functional Theory, (4) data-driven
molecular simulation, biomolecular force fields, molecular fragmentation,
and biomolecular simulation structural validation. They closely follow the
work of Ilyes Batatia, Bingqing Cheng, Mark E. Tuckerman, and Michele Ceriotti.\
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
Use <h2> for "Today's Computational Chemistry Digest — {today}"
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
