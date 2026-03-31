"""
Raw input parser for Workflow 1.
Accepts voice memo transcripts, bullet points, Slack messages, or rough paragraphs
and normalizes them into a structured input object for the content engine.
"""
import re
from dataclasses import dataclass, field


@dataclass
class ParsedInput:
    """Normalized representation of raw founder input."""
    raw_text: str
    input_type: str          # voice_memo | bullets | slack | paragraph
    founder: str             # itay | tory
    key_points: list[str] = field(default_factory=list)
    stats_mentioned: list[str] = field(default_factory=list)
    companies_mentioned: list[str] = field(default_factory=list)
    events_mentioned: list[str] = field(default_factory=list)
    products_referenced: list[str] = field(default_factory=list)
    estimated_urgency: str = "normal"   # low | normal | high
    word_count: int = 0


def detect_input_type(text: str) -> str:
    """Heuristic classification of raw input format."""
    stripped = text.strip()

    # Bullet points: lines starting with - or *
    bullet_lines = [l for l in stripped.split("\n") if l.strip().startswith(("-", "*", "•"))]
    if len(bullet_lines) >= 3 and len(bullet_lines) / max(len(stripped.split("\n")), 1) > 0.5:
        return "bullets"

    # Voice memo: long, single block, conversational markers
    voice_markers = ["so ", "like ", "literally", "you know", "i was", "i think", "the thing is",
                     "just got", "basically", "that's"]
    lower = stripped.lower()
    voice_score = sum(1 for m in voice_markers if m in lower)
    if voice_score >= 3 and len(stripped.split()) > 80:
        return "voice_memo"

    # Slack: shorter, informal, often starts with action
    if len(stripped.split()) < 120 and any(m in lower for m in ["just got back", "hey ", "fyi", "heads up"]):
        return "slack"

    # Default: paragraph
    return "paragraph"


def extract_stats(text: str) -> list[str]:
    """Pull out statistical references (percentages, dollar amounts, etc.)."""
    patterns = [
        r'\$[\d,.]+\s*(?:billion|B|million|M|trillion|T)\b',
        r'\d+\.?\d*\s*%',
        r'\$\d[\d,.]*',
        r'\d+\s*(?:basis points|bps)',
    ]
    stats = []
    for p in patterns:
        stats.extend(re.findall(p, text, re.IGNORECASE))
    return list(dict.fromkeys(stats))  # dedupe preserving order


def extract_companies(text: str) -> list[str]:
    """Identify company/firm mentions."""
    known = [
        "BlackRock", "Citadel", "Bridgewater", "Two Sigma", "DE Shaw",
        "iCapital", "CAIS", "Goldman Sachs", "Morgan Stanley", "JPMorgan",
        "Fidelity", "Schwab", "Vanguard", "Apollo", "KKR", "Ares",
        "Titan Investors",
    ]
    found = [c for c in known if c.lower() in text.lower()]
    return found


def extract_events(text: str) -> list[str]:
    """Identify event/conference mentions."""
    known_events = [
        "Titan Investors", "CAIS", "iCapital", "Future Proof",
        "Wealth Management EDGE", "Inside ETFs", "Morningstar",
        "Schwab IMPACT", "T3",
    ]
    found = [e for e in known_events if e.lower() in text.lower()]
    return found


def extract_products(text: str) -> list[str]:
    """Detect Equi product references."""
    products = []
    lower = text.lower()
    if any(p in lower for p in ["fund of funds", "fund-of-funds", "fof"]):
        products.append("Custom Fund of Funds")
    if "tender offer" in lower:
        products.append("Tender Offer Fund")
    if any(p in lower for p in ["branded fund", "multi-strategy", "absolute return"]):
        products.append("Equi Branded Private Funds")
    if "private credit" in lower:
        products.append("Private Credit")
    if "portable alpha" in lower:
        products.append("Portable Alpha")
    return products


def assess_urgency(text: str) -> str:
    """Estimate content urgency based on language cues."""
    lower = text.lower()
    high_signals = ["breaking", "just announced", "this morning", "urgent",
                    "game-changer", "right now", "today"]
    if any(s in lower for s in high_signals):
        return "high"
    low_signals = ["been thinking", "long term", "over time", "eventually"]
    if any(s in lower for s in low_signals):
        return "low"
    return "normal"


def parse_raw_input(text: str, founder: str = "tory") -> ParsedInput:
    """
    Parse raw founder input into a structured object.

    Args:
        text: Raw text (voice memo, bullets, Slack message, paragraph)
        founder: Founder key — 'itay' or 'tory'

    Returns:
        ParsedInput with extracted metadata
    """
    input_type = detect_input_type(text)

    # Extract key points based on format
    key_points = []
    if input_type == "bullets":
        for line in text.strip().split("\n"):
            cleaned = line.strip().lstrip("-*•").strip()
            if cleaned:
                key_points.append(cleaned)
    else:
        # For prose, split into sentences and take the most substantive ones
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        for s in sentences:
            words = s.split()
            if len(words) >= 8:  # Skip very short sentences
                key_points.append(s.strip())

    return ParsedInput(
        raw_text=text.strip(),
        input_type=input_type,
        founder=founder.lower(),
        key_points=key_points,
        stats_mentioned=extract_stats(text),
        companies_mentioned=extract_companies(text),
        events_mentioned=extract_events(text),
        products_referenced=extract_products(text),
        estimated_urgency=assess_urgency(text),
        word_count=len(text.split()),
    )
