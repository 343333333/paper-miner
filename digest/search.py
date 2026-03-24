"""Fetch recent papers from arXiv, PubMed, and ChemRxiv."""

import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

from config import (
    ARXIV_CATEGORIES, ARXIV_MAX_RESULTS, AUTHOR_NAMES,
    CHEMRXIV_CATEGORY_IDS, CHEMRXIV_MAX_RESULTS,
    LOOKBACK_DAYS, PUBMED_MAX_RESULTS, TOPIC_KEYWORDS,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _normalize_title(title: str) -> str:
    """Lowercase and strip punctuation for deduplication."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


# ------------------------------------------------------------------
# arXiv
# ------------------------------------------------------------------

ARXIV_API = "http://export.arxiv.org/api/query"

def _build_arxiv_query() -> str:
    """Build arXiv query string combining categories, keywords, and authors."""
    cat_query = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    # Pick a representative subset to keep the URL manageable
    kw_subset = TOPIC_KEYWORDS[:20]
    kw_parts = [f'abs:"{kw}"' for kw in kw_subset]
    au_parts = [f'au:"{name}"' for name in AUTHOR_NAMES]
    match_query = " OR ".join(kw_parts + au_parts)
    return f"({cat_query}) AND ({match_query})"


def fetch_arxiv_papers() -> list[dict]:
    """Return papers from arXiv published within the lookback window."""
    query = _build_arxiv_query()
    params = {
        "search_query": query,
        "start": 0,
        "max_results": ARXIV_MAX_RESULTS,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(resp.text)
    papers = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", "", ns).replace("\n", " ").strip()
        abstract = entry.findtext("atom:summary", "", ns).replace("\n", " ").strip()
        published_str = entry.findtext("atom:published", "", ns)
        arxiv_id_raw = entry.findtext("atom:id", "", ns)

        # Filter out papers older than the lookback window
        if published_str:
            try:
                pub_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                if pub_dt < cutoff:
                    continue
            except ValueError:
                pass  # keep papers with unparseable dates

        # Extract clean arXiv ID (e.g. "2403.12345")
        arxiv_id_match = re.search(r"abs/([^\s]+)$", arxiv_id_raw or "")
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else arxiv_id_raw

        authors = [
            a.findtext("atom:name", "", ns)
            for a in entry.findall("atom:author", ns)
        ]

        papers.append({
            "id": f"arxiv:{arxiv_id}",
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published_str,
            "source": "arXiv",
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "_norm_title": _normalize_title(title),
        })

    return papers


# ------------------------------------------------------------------
# PubMed
# ------------------------------------------------------------------

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def _build_pubmed_query() -> str:
    """Build PubMed search query from topic keywords and author names."""
    kw_terms = [f'"{kw}"[Title/Abstract]' for kw in TOPIC_KEYWORDS[:15]]
    au_terms = [f'"{name}"[Author]' for name in AUTHOR_NAMES]
    return " OR ".join(kw_terms + au_terms)


def fetch_pubmed_papers() -> list[dict]:
    """Return papers from PubMed published within the lookback window."""
    query = _build_pubmed_query()

    # Step 1: esearch — get PMIDs
    esearch_params = {
        "db": "pubmed",
        "term": query,
        "retmax": PUBMED_MAX_RESULTS,
        "reldate": LOOKBACK_DAYS,
        "datetype": "pdat",
        "retmode": "json",
    }
    esearch_resp = requests.get(
        f"{EUTILS_BASE}/esearch.fcgi",
        params=esearch_params,
        timeout=30,
    )
    esearch_resp.raise_for_status()
    id_list = esearch_resp.json().get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return []

    # Step 2: efetch — get full records
    time.sleep(0.5)  # be polite to NCBI
    efetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "rettype": "abstract",
        "retmode": "xml",
    }
    efetch_resp = requests.get(
        f"{EUTILS_BASE}/efetch.fcgi",
        params=efetch_params,
        timeout=30,
    )
    efetch_resp.raise_for_status()

    root = ET.fromstring(efetch_resp.text)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        pmid = pmid_el.text if pmid_el is not None else "unknown"

        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""

        abstract_els = article.findall(".//AbstractText")
        abstract = " ".join("".join(el.itertext()) for el in abstract_els)

        pub_date_el = article.find(".//PubDate")
        if pub_date_el is not None:
            year = pub_date_el.findtext("Year", "")
            month = pub_date_el.findtext("Month", "")
            day = pub_date_el.findtext("Day", "")
            published = f"{year}-{month}-{day}".strip("-")
        else:
            published = ""

        author_els = article.findall(".//Author")
        authors = []
        for a in author_els:
            last = a.findtext("LastName", "")
            fore = a.findtext("ForeName", "")
            if last:
                authors.append(f"{fore} {last}".strip())

        papers.append({
            "id": f"pubmed:{pmid}",
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "source": "PubMed",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "_norm_title": _normalize_title(title),
        })

    return papers


# ------------------------------------------------------------------
# ChemRxiv
# ------------------------------------------------------------------

CHEMRXIV_API = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"

def fetch_chemrxiv_papers() -> list[dict]:
    """Return papers from ChemRxiv published within the lookback window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    date_from = cutoff.strftime("%Y-%m-%dT00:00:00.000Z")

    query_parts = [
        f"limit={CHEMRXIV_MAX_RESULTS}",
        "skip=0",
        "sort=PUBLISHED_DATE_DESC",
        f"searchDateFrom={date_from}",
    ]
    for cat_id in CHEMRXIV_CATEGORY_IDS:
        query_parts.append(f"categoryIds={cat_id}")

    url = f"{CHEMRXIV_API}?{'&'.join(query_parts)}"
    headers = {"User-Agent": "paper-miner/1.0 (research digest bot)"}
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 403:
        print("  ChemRxiv: blocked by Cloudflare (may work from GitHub Actions)")
        return []
    resp.raise_for_status()

    data = resp.json()
    items = data.get("itemHits", [])
    papers = []

    for hit in items:
        item = hit.get("item", hit)
        title = item.get("title", "")
        abstract = item.get("abstract", "")
        item_id = item.get("id", "")
        doi = item.get("doi", "")
        published = item.get("statusDate", "")

        authors = []
        for a in item.get("authors", []):
            first = a.get("firstName", "")
            last = a.get("lastName", "")
            if last:
                authors.append(f"{first} {last}".strip())

        papers.append({
            "id": f"chemrxiv:{doi or item_id}",
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "source": "ChemRxiv",
            "url": f"https://chemrxiv.org/engage/chemrxiv/article-details/{item_id}",
            "_norm_title": _normalize_title(title),
        })

    return papers


# ------------------------------------------------------------------
# Combined search with cross-source deduplication
# ------------------------------------------------------------------

def fetch_all_papers() -> list[dict]:
    """Fetch from arXiv, PubMed, and ChemRxiv, deduplicate by normalized title."""
    print("Fetching from arXiv...")
    arxiv_papers = fetch_arxiv_papers()
    print(f"  arXiv: {len(arxiv_papers)} papers")

    print("Fetching from PubMed...")
    pubmed_papers = fetch_pubmed_papers()
    print(f"  PubMed: {len(pubmed_papers)} papers")

    print("Fetching from ChemRxiv...")
    chemrxiv_papers = fetch_chemrxiv_papers()
    print(f"  ChemRxiv: {len(chemrxiv_papers)} papers")

    # Deduplicate across sources by normalized title
    seen_titles: set[str] = set()
    combined: list[dict] = []
    for p in arxiv_papers + pubmed_papers + chemrxiv_papers:
        nt = p["_norm_title"]
        if nt and nt not in seen_titles:
            seen_titles.add(nt)
            combined.append(p)

    print(f"  Combined (after cross-source dedup): {len(combined)} papers")
    return combined
