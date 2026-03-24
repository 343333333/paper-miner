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

    # Cluster C - Key researchers
    "Ilyes Batatia",
    "Mingyuan Zhang"
)

# Scoring
SCORE_THRESHOLD = 7          # Papers below this are discarded
MAX_DIGEST_PAPERS = 8        # Max papers sent in one digest

# Search limits
ARXIV_MAX_RESULTS = 50
PUBMED_MAX_RESULTS = 50

# API model names
HAIKU_MODEL = "claude-haiku-4-5"
SONNET_MODEL = "claude-sonnet-4-20250514"
