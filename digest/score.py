"""Score paper relevance using Claude Haiku."""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from config import HAIKU_MODEL, SCORE_THRESHOLD

SYSTEM_PROMPT = """\
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

KEY RESEARCHERS whose work is always relevant: Erwin Frey, Nigel Goldenfeld.\
"""

USER_TEMPLATE = """\
Paper title: {title}
Abstract: {abstract}

Return a JSON object with:
- "score": integer 0–10
- "topics": list of matched topic keywords (e.g. ["condensate", "Cahn-Hilliard"])
- "reason": one sentence explaining the score
- "dynamic_boundary": true if the paper involves concentration fields coupled
  to moving or dynamic boundaries/membranes/DNA (add 2 bonus points to score)

Return only valid JSON. No markdown.\
"""


def _score_paper(client: anthropic.Anthropic, paper: dict) -> dict:
    """Call Claude Haiku to score a single paper. Returns paper with score fields added."""
    user_msg = USER_TEMPLATE.format(
        title=paper["title"],
        abstract=paper["abstract"] or "(no abstract)",
    )
    try:
        message = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
    except Exception as e:
        print(f"  [score] Error scoring '{paper['title'][:60]}': {e}")
        result = {"score": 0, "topics": [], "reason": "scoring error", "dynamic_boundary": False}

    base_score = int(result.get("score", 0))
    dynamic_boundary = bool(result.get("dynamic_boundary", False))
    topics = result.get("topics", [])

    # Apply bonuses
    bonus = 0
    if dynamic_boundary:
        bonus += 2
    if len(topics) >= 2:
        bonus += 2
    final_score = min(10, base_score + bonus)

    return {
        **paper,
        "score": final_score,
        "base_score": base_score,
        "topics": topics,
        "reason": result.get("reason", ""),
        "dynamic_boundary": dynamic_boundary,
    }


def score_papers(papers: list[dict]) -> list[dict]:
    """Score all papers in parallel batches of 10. Returns only papers >= threshold."""
    if not papers:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    client = anthropic.Anthropic(api_key=api_key)

    BATCH_SIZE = 10
    scored: list[dict] = []

    for batch_start in range(0, len(papers), BATCH_SIZE):
        batch = papers[batch_start: batch_start + BATCH_SIZE]
        print(f"  Scoring papers {batch_start + 1}–{batch_start + len(batch)} of {len(papers)}...")
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = {executor.submit(_score_paper, client, p): p for p in batch}
            for future in as_completed(futures):
                scored.append(future.result())

    # Filter and sort
    relevant = [p for p in scored if p["score"] >= SCORE_THRESHOLD]
    relevant.sort(key=lambda p: p["score"], reverse=True)
    print(f"  {len(relevant)} papers scored >= {SCORE_THRESHOLD} (out of {len(scored)} scored)")
    return relevant
