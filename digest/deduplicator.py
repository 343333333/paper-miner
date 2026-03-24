"""Read/write seen_papers.json to skip already-sent papers."""

import json
import os
from datetime import date
from pathlib import Path

SEEN_PAPERS_PATH = Path(__file__).parent.parent / "data" / "seen_papers.json"


def load_seen_ids() -> set[str]:
    """Return the set of paper IDs already sent."""
    if not SEEN_PAPERS_PATH.exists():
        return set()
    with open(SEEN_PAPERS_PATH) as f:
        data = json.load(f)
    return {p["id"] for p in data.get("papers", [])}


def filter_new_papers(papers: list[dict]) -> list[dict]:
    """Remove papers whose IDs are already in seen_papers.json."""
    seen = load_seen_ids()
    new = [p for p in papers if p["id"] not in seen]
    skipped = len(papers) - len(new)
    if skipped:
        print(f"  Deduplicator: skipped {skipped} already-seen papers")
    return new


def mark_papers_sent(papers: list[dict]) -> None:
    """Append sent paper IDs to seen_papers.json."""
    if not papers:
        return

    # Load existing
    if SEEN_PAPERS_PATH.exists():
        with open(SEEN_PAPERS_PATH) as f:
            data = json.load(f)
    else:
        data = {"papers": []}

    today = date.today().isoformat()
    for p in papers:
        data["papers"].append({
            "id": p["id"],
            "title": p["title"],
            "sent_date": today,
        })

    SEEN_PAPERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_PAPERS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved {len(papers)} new paper IDs to seen_papers.json")
