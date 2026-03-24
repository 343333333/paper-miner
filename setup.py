#!/usr/bin/env python3
"""Interactive setup script for paper-digest. No external dependencies."""

import os
import re
import sys

# ── ANSI colours (disabled on non-TTY) ────────────────────────────────────────
USE_COLOR = sys.stdout.isatty()

def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

def bold(t):   return c(t, "1")
def green(t):  return c(t, "32")
def cyan(t):   return c(t, "36")
def yellow(t): return c(t, "33")
def dim(t):    return c(t, "2")


# ── Helpers ────────────────────────────────────────────────────────────────────

def ask(prompt, default=None):
    """Single-line prompt; returns default on empty input."""
    hint = f" [{default}]" if default is not None else ""
    try:
        value = input(f"{prompt}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return value if value else (default if default is not None else "")


def ask_int(prompt, default, lo=1, hi=9999):
    while True:
        raw = ask(prompt, str(default))
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"  Please enter a number between {lo} and {hi}.")


def ask_choice(prompt, options):
    """
    Display a numbered list and return the (0-based) index chosen.
    options: list of strings
    """
    for i, opt in enumerate(options, 1):
        print(f"  {bold(str(i))}) {opt}")
    while True:
        raw = ask(prompt, "1")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        except ValueError:
            pass
        print(f"  Please enter a number between 1 and {len(options)}.")


def divider():
    print(dim("─" * 60))


# ── Timezone table ─────────────────────────────────────────────────────────────
# (label, UTC offset in hours, IANA name for display)
TIMEZONES = [
    ("UTC+0  — London / Lisbon",           0),
    ("UTC+1  — Paris / Berlin / Rome",     1),
    ("UTC+2  — Cairo / Helsinki / Athens", 2),
    ("UTC+3  — Moscow / Nairobi",          3),
    ("UTC+4  — Dubai / Baku",              4),
    ("UTC+5  — Karachi / Tashkent",        5),
    ("UTC+5:30 — New Delhi / Mumbai",      5.5),
    ("UTC+6  — Dhaka / Almaty",            6),
    ("UTC+7  — Bangkok / Jakarta",         7),
    ("UTC+8  — Beijing / Singapore / HK",  8),
    ("UTC+9  — Tokyo / Seoul",             9),
    ("UTC+10 — Sydney / Melbourne",        10),
    ("UTC+12 — Auckland",                  12),
    ("UTC-5  — New York / Toronto",        -5),
    ("UTC-6  — Chicago / Mexico City",     -6),
    ("UTC-7  — Denver / Phoenix",          -7),
    ("UTC-8  — Los Angeles / Vancouver",   -8),
    ("UTC-3  — São Paulo / Buenos Aires",  -3),
]


def utc_hour_for_8am(utc_offset: float) -> int:
    """Return the UTC hour (0-23) that corresponds to 08:00 local time."""
    utc = (8 - utc_offset) % 24
    return int(utc)


# ── cron builder ──────────────────────────────────────────────────────────────

def build_cron(frequency_idx: int, utc_hour: int) -> str:
    """
    frequency_idx: 0=daily, 1=every-3-days, 2=weekly (Monday)
    Returns a 5-field cron string.
    """
    if frequency_idx == 0:
        return f"0 {utc_hour} * * *"
    elif frequency_idx == 1:
        return f"0 {utc_hour} */3 * *"
    else:  # weekly — Monday
        return f"0 {utc_hour} * * 1"


# ── File updaters ──────────────────────────────────────────────────────────────

def update_config(topics: list[str], authors: list[str], max_papers: int, lookback_days: int):
    """Overwrite TOPIC_KEYWORDS, AUTHOR_NAMES, MAX_DIGEST_PAPERS, and LOOKBACK_DAYS in config.py."""
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    with open(config_path, "r") as f:
        src = f.read()

    # Replace TOPIC_KEYWORDS list
    keywords_lines = ",\n    ".join(f'"{t}"' for t in topics)
    new_block = f"TOPIC_KEYWORDS = [\n    {keywords_lines},\n]"
    src = re.sub(
        r"TOPIC_KEYWORDS\s*=\s*\[.*?\]",
        new_block,
        src,
        flags=re.DOTALL,
    )

    # Replace AUTHOR_NAMES list
    if authors:
        authors_lines = ",\n    ".join(f'"{a}"' for a in authors)
        new_authors = f"AUTHOR_NAMES = [\n    {authors_lines},\n]"
    else:
        new_authors = "AUTHOR_NAMES = []"
    src = re.sub(
        r"AUTHOR_NAMES\s*=\s*\[.*?\]",
        new_authors,
        src,
        flags=re.DOTALL,
    )

    # Replace MAX_DIGEST_PAPERS
    src = re.sub(
        r"(MAX_DIGEST_PAPERS\s*=\s*)\d+",
        rf"\g<1>{max_papers}",
        src,
    )

    # Replace LOOKBACK_DAYS
    src = re.sub(
        r"(LOOKBACK_DAYS\s*=\s*)\d+",
        rf"\g<1>{lookback_days}",
        src,
    )

    with open(config_path, "w") as f:
        f.write(src)


def update_workflow_cron(cron_expr: str):
    """Replace the cron schedule line in daily_digest.yml."""
    yml_path = os.path.join(
        os.path.dirname(__file__), ".github", "workflows", "daily_digest.yml"
    )
    with open(yml_path, "r") as f:
        src = f.read()

    src = re.sub(
        r"(- cron:\s*')[^']+(')",
        rf"\g<1>{cron_expr}\g<2>",
        src,
    )

    with open(yml_path, "w") as f:
        f.write(src)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print()
    print(bold(cyan("  paper-digest setup")))
    print(dim("  Configure your personalised arXiv digest in ~2 minutes."))
    print()

    # ── 1. Research interests ─────────────────────────────────────────────────
    divider()
    print(bold("Step 1 — Research interests"))
    print(dim("Enter topics/keywords one per line. Empty line when done."))
    print(dim("These are used to find and score papers from arXiv/PubMed."))
    print()
    topics = []
    while True:
        try:
            line = input(f"  Topic {len(topics)+1}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not line:
            if not topics:
                print("  Please enter at least one topic.")
                continue
            break
        topics.append(line)
    print()

    # ── 2. Author names ──────────────────────────────────────────────────────
    divider()
    print(bold("Step 2 — Researchers to follow"))
    print(dim("Enter author names one per line. Empty line when done."))
    print(dim("Papers by these authors will be found via the author field."))
    print()
    authors = []
    while True:
        try:
            line = input(f"  Author {len(authors)+1}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not line:
            break
        authors.append(line)
    print()

    # ── 3. Max papers per digest ──────────────────────────────────────────────
    divider()
    print(bold("Step 3 — Maximum papers per digest"))
    max_papers = ask_int("  How many papers max per digest", default=8, lo=1, hi=50)
    print()

    # ── 4. Delivery frequency ─────────────────────────────────────────────────
    divider()
    print(bold("Step 4 — Delivery frequency"))
    FREQ_OPTIONS = ["Every day", "Every 3 days", "Weekly (Mondays)"]
    freq_idx = ask_choice("  Choose a frequency", FREQ_OPTIONS)
    print()

    # ── 5. Timezone ───────────────────────────────────────────────────────────
    divider()
    print(bold("Step 5 — Timezone"))
    print(dim("  Digest will be delivered at 08:00 your local time."))
    print()
    tz_labels = [label for label, _ in TIMEZONES]
    tz_idx = ask_choice("  Your timezone", tz_labels)
    tz_label, utc_offset = TIMEZONES[tz_idx]
    utc_hour = utc_hour_for_8am(utc_offset)
    print()

    # ── 6. Recipient email ────────────────────────────────────────────────────
    divider()
    print(bold("Step 6 — Recipient email"))
    while True:
        email = ask("  Your email address")
        if "@" in email and "." in email.split("@")[-1]:
            break
        print("  That doesn't look like a valid email address.")
    print()

    # ── Build cron and lookback ──────────────────────────────────────────────
    cron_expr = build_cron(freq_idx, utc_hour)
    FREQ_TO_LOOKBACK = {0: 1, 1: 3, 2: 7}  # daily=1, every-3-days=3, weekly=7
    lookback_days = FREQ_TO_LOOKBACK[freq_idx]

    # ── Write files ───────────────────────────────────────────────────────────
    divider()
    print(bold("Saving configuration…"))
    try:
        update_config(topics, authors, max_papers, lookback_days)
        print(f"  {green('✓')} config.py updated")
    except Exception as e:
        print(f"  ✗ Failed to update config.py: {e}")

    try:
        update_workflow_cron(cron_expr)
        print(f"  {green('✓')} .github/workflows/daily_digest.yml updated")
    except Exception as e:
        print(f"  ✗ Failed to update workflow: {e}")
    print()

    # ── Summary ───────────────────────────────────────────────────────────────
    divider()
    print(bold("Summary"))
    print()
    print(f"  {'Topics:':<22} {', '.join(topics)}")
    print(f"  {'Authors:':<22} {', '.join(authors) if authors else '(none)'}")
    print(f"  {'Max papers:':<22} {max_papers}")
    print(f"  {'Lookback:':<22} {lookback_days} day{'s' if lookback_days > 1 else ''}")
    print(f"  {'Frequency:':<22} {FREQ_OPTIONS[freq_idx]}")
    print(f"  {'Timezone:':<22} {tz_label.strip()}")
    print(f"  {'Send time:':<22} 08:00 local  (UTC {utc_hour:02d}:00)")
    print(f"  {'Cron expression:':<22} {cron_expr}")
    print(f"  {'Recipient email:':<22} {email}")
    print()

    # ── Secrets reminder ──────────────────────────────────────────────────────
    divider()
    print(bold("GitHub Secrets you still need to set"))
    print()
    secrets = [
        ("ANTHROPIC_API_KEY",  "Your Anthropic API key"),
        ("GMAIL_ADDRESS",      "Gmail address used to send the digest"),
        ("GMAIL_APP_PASSWORD", "Gmail App Password (not your login password)"),
        ("RECIPIENT_EMAIL",    f"Recipient address — {email}"),
    ]
    for name, desc in secrets:
        print(f"  {yellow(name)}")
        print(f"    {dim(desc)}")
    print()
    print(
        f"  Set them at: {cyan('https://github.com/<your-username>/<your-repo>/settings/secrets/actions')}"
    )
    print()
    divider()
    print(bold(green("Setup complete. Commit the updated files and push to activate.")))
    print()


if __name__ == "__main__":
    main()
