"""Configuration: topics, scoring thresholds, search parameters."""
# arXiv categories to search
ARXIV_CATEGORIES = ["physics.chem-ph", "cond-mat.soft", "q-bio.BM", "cs.LG", "physics.bio-ph"]

# Topic keywords used to build search queries
TOPIC_KEYWORDS = [
    # Cluster A - Many-body and data-driven potentials
    "many-body potential",
    "permutationally invariant polynomial",
    "biomolecular force field",
    "many-body expansion",
    "data-driven molecular simulation",
    "Tensorial Model",
    "Markov State Models",
    # Cluster B - Machine learning force fields
    "CCSD(T) machine learning",
    "intramolecular fragmentation",
    "MACE polarizable",
    "universal interatomic potential",
    "FAIR atomistic simulation",
    "equivariant neural network potential",
]

# Author names — searched in the author field (not abstract)
AUTHOR_NAMES = [
    "Ilyes Batatia",
    "Mingyuan Zhang",
]

# Scoring
SCORE_THRESHOLD = 7          # Papers below this are discarded
MAX_DIGEST_PAPERS = 8        # Max papers sent in one digest

# ChemRxiv categories (Physical Chemistry, Theoretical and Computational Chemistry)
CHEMRXIV_CATEGORY_IDS = [
    "605c72ef153207001f6470cf",  # Physical Chemistry
    "605c72ef153207001f6470ce",  # Theoretical and Computational Chemistry
]

# Search limits
ARXIV_MAX_RESULTS = 50
PUBMED_MAX_RESULTS = 50
CHEMRXIV_MAX_RESULTS = 50
LOOKBACK_DAYS = 3            # How many days back to search (matches delivery frequency)

# API model names
HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-4-20250514"
