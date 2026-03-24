"""Configuration: topics, scoring thresholds, search parameters."""

# arXiv categories to search
ARXIV_CATEGORIES = ["q-bio.SC", "q-bio.CB", "physics.bio-ph", "cond-mat.soft"]

# Topic keywords used to build search queries
TOPIC_KEYWORDS = [
    # Cluster A - Biological systems
    "COPII vesicle", "ER transport", "ER-to-Golgi", "secretory pathway",
    "cargo sorting", "membrane curvature",
    "ER-mitochondria", "MAM", "mitochondria-associated membrane",
    "MFN2", "VDAC", "IP3R", "lipid transfer", "calcium signaling",
    "organelle contact site", "organelle tethering",
    "biomolecular condensate", "phase separation", "liquid-liquid phase separation",
    "LLPS", "transcriptional condensate", "protein-DNA condensate",
    "coarsening dynamics",
    # Cluster B - Theoretical methods
    "phase-field", "Cahn-Hilliard", "Model B dynamics", "Flory-Huggins",
    "chemical potential", "field-theoretic",
    "reaction-diffusion", "Turing instability", "pattern formation",
    "activator-inhibitor", "morphogenesis", "Min protein",
    "active matter", "nonequilibrium", "Onsager", "entropy production",
    "fluctuation theorem", "active noise",
    # Cluster C - Key researchers
    "Erwin Frey", "Nigel Goldenfeld",
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
