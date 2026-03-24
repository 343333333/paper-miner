"""Entry point: orchestrates the full paper-digest pipeline."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (local development)
load_dotenv(Path(__file__).parent / ".env")


def run_search_only():
    from digest.search import fetch_all_papers
    papers = fetch_all_papers()
    print(f"\n{'='*60}")
    print(f"Total papers found: {len(papers)}")
    print(f"{'='*60}")
    for p in papers:
        print(f"[{p['source']:6}] {p['title'][:80]}")
    return papers


def run_score_only():
    from digest.search import fetch_all_papers
    from digest.deduplicator import filter_new_papers
    from digest.score import score_papers

    papers = fetch_all_papers()
    papers = filter_new_papers(papers)
    scored = score_papers(papers)

    print(f"\n{'='*60}")
    print(f"Scored papers (score >= threshold): {len(scored)}")
    print(f"{'='*60}")
    for p in scored:
        dyn = " [DYN]" if p.get("dynamic_boundary") else ""
        print(f"  [{p['score']:2}]{dyn} {p['title'][:70]}")
        print(f"       Topics: {', '.join(p.get('topics', []))}")
        print(f"       Reason: {p.get('reason', '')}")
    return scored


def run_summarize_only():
    from digest.search import fetch_all_papers
    from digest.deduplicator import filter_new_papers
    from digest.score import score_papers
    from digest.summarize import generate_digest

    papers = fetch_all_papers()
    papers = filter_new_papers(papers)
    scored = score_papers(papers)

    if not scored:
        print("No papers scored above threshold — nothing to summarize.")
        return None

    html = generate_digest(scored)
    print("\n" + "=" * 60)
    print("HTML DIGEST:")
    print("=" * 60)
    print(html)
    return html


def run_test_email():
    """Send a test email with dummy content (no API calls)."""
    from digest.email_sender import send_digest

    dummy_html = """\
<h2>Today's Biophysics Digest — Test</h2>
<h3><a href="https://arxiv.org/abs/test">Test Paper: Phase-field model of condensate formation</a></h3>
<p><strong>Summary:</strong> This is a test email from the paper-digest pipeline.</p>
<p><strong>Relevance:</strong> Directly relevant to phase-field / Cahn-Hilliard work on condensates.</p>
<p><strong>Methodology:</strong> Theoretical / analytical.</p>
<hr>
"""
    send_digest(dummy_html, n_papers=1)


def run_full_pipeline():
    from digest.search import fetch_all_papers
    from digest.deduplicator import filter_new_papers, mark_papers_sent
    from digest.score import score_papers
    from digest.summarize import generate_digest
    from digest.email_sender import send_digest, send_no_papers_email

    print("=== Step 1: Fetching papers ===")
    papers = fetch_all_papers()

    print("\n=== Step 2: Filtering already-seen papers ===")
    papers = filter_new_papers(papers)
    print(f"  {len(papers)} new papers to process")

    if not papers:
        print("No new papers today.")
        send_no_papers_email()
        return

    print("\n=== Step 3: Scoring papers ===")
    scored = score_papers(papers)

    if not scored:
        print("No papers scored above threshold.")
        send_no_papers_email()
        return

    print("\n=== Step 4: Generating digest ===")
    html = generate_digest(scored)

    print("\n=== Step 5: Sending email ===")
    send_digest(html, n_papers=len(scored))

    print("\n=== Step 6: Marking papers as sent ===")
    mark_papers_sent(scored)

    print("\nDone.")


def main():
    parser = argparse.ArgumentParser(description="Daily biophysics paper digest")
    parser.add_argument("--search-only", action="store_true", help="Fetch and print papers only")
    parser.add_argument("--score-only", action="store_true", help="Fetch, filter, score, and print")
    parser.add_argument("--summarize-only", action="store_true", help="Full pipeline up to HTML generation")
    parser.add_argument("--test", action="store_true", help="Send a test email with dummy content")
    args = parser.parse_args()

    if args.search_only:
        run_search_only()
    elif args.score_only:
        run_score_only()
    elif args.summarize_only:
        run_summarize_only()
    elif args.test:
        run_test_email()
    else:
        run_full_pipeline()


if __name__ == "__main__":
    main()
