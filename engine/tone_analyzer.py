"""
Tone analyzer — detects topic, market context, urgency, and recommended angle.
Runs before content generation to inform platform-specific output.
"""
from dataclasses import dataclass, field


@dataclass
class ToneAnalysis:
    """Analysis of input content for generation guidance."""
    primary_topic: str
    secondary_topics: list[str] = field(default_factory=list)
    market_context: str = ""
    urgency: str = "normal"
    recommended_angle: str = ""
    data_density: str = "medium"     # low | medium | high
    sentiment: str = "neutral"       # bullish | neutral | cautious | urgent
    suggested_hashtags: list[str] = field(default_factory=list)
    hook_suggestions: list[str] = field(default_factory=list)


# Topic detection rules
TOPIC_RULES = [
    {
        "topic": "Correlation Breakdown & 60/40 Failure",
        "keywords": ["correlation", "60/40", "stocks and bonds", "diversification failure"],
        "angle": "The traditional portfolio is broken — here's the data and what to do about it",
        "hashtags": ["#Diversification", "#PortfolioConstruction", "#Correlation"],
        "sentiment": "urgent",
    },
    {
        "topic": "Hedge Fund Access for RIAs",
        "keywords": ["hedge fund", "ria access", "institutional hedge fund", "alternatives access"],
        "angle": "The access gap is real — and it's costing your clients returns",
        "hashtags": ["#HedgeFunds", "#RIA", "#AltsAccess"],
        "sentiment": "bullish",
    },
    {
        "topic": "Industry Validation & Momentum",
        "keywords": ["blackrock", "inflows", "net inflows", "validates", "industry momentum"],
        "angle": "The smart money is moving — and independent advisors can't afford to wait",
        "hashtags": ["#AlternativeInvestments", "#InstitutionalInvesting", "#HedgeFunds"],
        "sentiment": "bullish",
    },
    {
        "topic": "Conference & Advisor Sentiment",
        "keywords": ["conference", "roundtable", "advisor", "event", "spoke to", "energy"],
        "angle": "On the ground with advisors: what they're saying about alternatives",
        "hashtags": ["#WealthManagement", "#AdvisorInsights", "#AlternativeInvestments"],
        "sentiment": "bullish",
    },
    {
        "topic": "Tender Offer Fund Launch",
        "keywords": ["tender offer", "registered fund", "launching", "game-changer"],
        "angle": "A new vehicle that simplifies alternatives for every RIA",
        "hashtags": ["#FundOfFunds", "#RIA", "#InnovationInFinance"],
        "sentiment": "bullish",
    },
    {
        "topic": "Private Credit Opportunity",
        "keywords": ["private credit", "direct lending", "yield", "fixed income alternative"],
        "angle": "Private credit is having a moment — here's why it belongs in advisor portfolios",
        "hashtags": ["#PrivateCredit", "#AlternativeInvestments", "#Yield"],
        "sentiment": "bullish",
    },
    {
        "topic": "Operational Infrastructure Gap",
        "keywords": ["infrastructure", "operational", "lp agreement", "capital call", "nightmare"],
        "angle": "The hidden cost of DIY alternatives: operational complexity kills returns",
        "hashtags": ["#Operations", "#RIA", "#AlternativeInvestments"],
        "sentiment": "cautious",
    },
    {
        "topic": "Portfolio Construction & Risk",
        "keywords": ["portfolio construction", "risk-adjusted", "uncorrelated", "alpha", "dispersion"],
        "angle": "Building truly diversified portfolios requires more than asset class labels",
        "hashtags": ["#PortfolioConstruction", "#RiskManagement", "#Alpha"],
        "sentiment": "neutral",
    },
]


def analyze_tone(text: str, founder: str = "tory") -> ToneAnalysis:
    """
    Analyze raw input to determine topic, tone, and generation guidance.

    Args:
        text: Raw input text
        founder: Founder key for voice calibration

    Returns:
        ToneAnalysis with detected topics, angles, and suggestions
    """
    lower = text.lower()

    # Match topics by keyword presence
    matched_topics = []
    for rule in TOPIC_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in lower)
        if score > 0:
            matched_topics.append((score, rule))

    matched_topics.sort(key=lambda x: x[0], reverse=True)

    if not matched_topics:
        # Fallback
        return ToneAnalysis(
            primary_topic="General Market Commentary",
            recommended_angle="Equi's perspective on what matters for advisors today",
            suggested_hashtags=["#AlternativeInvestments", "#WealthManagement"],
        )

    primary = matched_topics[0][1]
    secondary = [m[1]["topic"] for m in matched_topics[1:4]]

    # Assess data density
    import re
    stat_count = len(re.findall(r'\d+\.?\d*\s*%|\$[\d,.]+\s*(?:billion|B|million|M)', text, re.IGNORECASE))
    if stat_count >= 3:
        data_density = "high"
    elif stat_count >= 1:
        data_density = "medium"
    else:
        data_density = "low"

    # Generate hook suggestions
    hooks = _generate_hooks(primary["topic"], text, founder)

    # Collect hashtags from all matched topics, deduped
    all_hashtags = []
    for _, rule in matched_topics:
        for tag in rule["hashtags"]:
            if tag not in all_hashtags:
                all_hashtags.append(tag)

    return ToneAnalysis(
        primary_topic=primary["topic"],
        secondary_topics=secondary,
        market_context=_extract_market_context(text),
        urgency=_assess_content_urgency(text),
        recommended_angle=primary["angle"],
        data_density=data_density,
        sentiment=primary["sentiment"],
        suggested_hashtags=all_hashtags[:6],
        hook_suggestions=hooks,
    )


def _extract_market_context(text: str) -> str:
    """Extract the market environment framing from the text."""
    lower = text.lower()
    contexts = []
    if "2022" in lower or "correlation" in lower:
        contexts.append("post-2022 correlation regime shift")
    if "inflows" in lower or "net inflows" in lower:
        contexts.append("hedge fund industry inflow momentum")
    if "blackrock" in lower:
        contexts.append("major allocator endorsement of alternatives")
    if "ria" in lower and ("growing" in lower or "trend" in lower):
        contexts.append("RIA industry shift toward alternatives")
    return "; ".join(contexts) if contexts else "current market environment"


def _assess_content_urgency(text: str) -> str:
    """Determine urgency for content publication timing."""
    lower = text.lower()
    if any(w in lower for w in ["just announced", "breaking", "this morning", "today"]):
        return "high"
    if any(w in lower for w in ["just got back", "this week", "recently"]):
        return "medium"
    return "normal"


def _generate_hooks(topic: str, text: str, founder: str) -> list[str]:
    """Generate opening hook suggestions based on topic and content."""
    hooks = []
    lower = text.lower()

    if "95%" in text or "correlation" in lower:
        hooks.append("In 2022, stocks and bonds had a 95% correlation. So much for diversification.")
    if "$21b" in lower or "inflow" in lower:
        hooks.append("$21B in net inflows to hedge funds in Q1 2025. The tide is turning.")
    if "blackrock" in lower:
        hooks.append("When BlackRock tells investors to increase hedge fund allocations, you listen.")
    if "titan" in lower or "conference" in lower or "roundtable" in lower:
        hooks.append("I just got back from a room full of the smartest advisors in the country. Here's what they're all saying.")
    if "tender offer" in lower:
        hooks.append("What if one allocation could give your clients a diversified hedge fund portfolio?")

    # Generic hooks if none matched
    if not hooks:
        hooks = [
            "The alternatives landscape is shifting. Here's what we're seeing.",
            "Every advisor I talk to is asking the same question.",
        ]

    return hooks
