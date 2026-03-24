"""Configuration: topics, scoring thresholds, search parameters."""

# arXiv categories to search
ARXIV_CATEGORIES = ["q-bio.SC", "q-bio.CB", "physics.bio-ph", "cond-mat.soft"]

# Topic keywords used to build search queries
TOPIC_KEYWORDS = [
    "machine learning potential in chemistry",
    "force field development for biochemical simulation",
    "machine learning potential(MACE UMA) in benchmark of polypeptide or protein simulation",
    "polarizable electrostatic foundation model",
    "biomolecular simulation structural validation",
    "equivariant graph neural network molecular dynamics",
    "machine learning interatomic potential transferability",
]

# Scoring
SCORE_THRESHOLD = 7          # Papers below this are discarded
MAX_DIGEST_PAPERS = 8        # Max papers sent in one digest

# Search limits
ARXIV_MAX_RESULTS = 50
PUBMED_MAX_RESULTS = 50

# API model names
HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-4-20250514"
