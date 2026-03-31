"""
Global configuration for the CEO Content Repurposing & Distribution Engine.
All tunable parameters live here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "content_engine.db"
OUTPUT_DIR = BASE_DIR / "output"
SAMPLE_DIR = BASE_DIR / "sample_data"

# ── API keys ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CONTENT_MAX_TOKENS = 4096

# ── Company context ─────────────────────────────────────────────────────────
COMPANY_NAME = "Equi"
COMPANY_LEGAL = "Equilibrium Ventures, LLC"
COMPANY_TAGLINE = "Wall Street expertise and Silicon Valley innovation"
LINKEDIN_HANDLE = "@joinequi"
TWITTER_HANDLE = "@join_equi"
WEBSITE = "https://www.joinequi.com"

COMPANY_DESCRIPTION = (
    "Equi builds fund-of-funds products — private credit, hedge fund, and "
    "portable alpha — for independent RIAs with $1B–$30B in AUM. We combine "
    "Wall Street expertise and Silicon Valley innovation to give advisors "
    "institutional-quality access to alternatives without the operational burden."
)

FOUNDERS = {
    "itay": {
        "name": "Itay",
        "title": "CIO",
        "full_title": "Chief Investment Officer",
        "linkedin": "Itay — CIO at Equi",
        "voice": "analytical, data-driven, references specific metrics and market dynamics",
    },
    "tory": {
        "name": "Tory",
        "title": "CEO",
        "full_title": "Chief Executive Officer",
        "linkedin": "Tory — CEO at Equi",
        "voice": "strategic, relationship-focused, connects market trends to advisor pain points",
    },
}

# ── Products ─────────────────────────────────────────────────────────────────
PRODUCTS = {
    "custom_fof": "Custom Fund of Funds for RIAs (private credit, hedge fund, portable alpha)",
    "branded_funds": "Equi Branded Private Funds (absolute return multi-strategy for family offices/institutions)",
    "tender_offer": "Tender Offer Fund (registered hedge fund of funds for RIA allocations — in registration)",
}

# ── Tone & brand ─────────────────────────────────────────────────────────────
BRAND_VOICE = (
    "Institutional but accessible — not stuffy, not salesy. Data-driven with specific "
    "market dynamics (correlations, dispersion, risk). Thought leadership framing: "
    "'Here's what we see and why it matters.' References industry events and platforms "
    "(Titan Investors, CAIS, iCapital). Uses phrases like 'Hidden Edge', 'absolute return', "
    "'uncorrelated'."
)

LINKEDIN_HASHTAGS = [
    "#AlternativeInvestments", "#HedgeFunds", "#Diversification",
    "#RIA", "#WealthManagement", "#PrivateCredit", "#PortableAlpha",
    "#InstitutionalInvesting", "#FundOfFunds", "#AltsAccess",
]

# ── Platform constraints ────────────────────────────────────────────────────
PLATFORM_SPECS = {
    "linkedin": {
        "name": "LinkedIn",
        "min_words": 500,
        "max_words": 800,
        "tone": "professional thought leadership, long-form, uses hashtags",
        "format": "paragraphs with line breaks, 3-5 hashtags at end",
    },
    "newsletter": {
        "name": "Newsletter Blurb",
        "min_words": 200,
        "max_words": 300,
        "tone": "punchy, informative, includes clear CTA",
        "format": "short paragraphs, bold key stats, CTA at end",
    },
    "twitter": {
        "name": "X/Twitter Thread",
        "min_tweets": 4,
        "max_tweets": 7,
        "max_chars_per_tweet": 280,
        "tone": "concise, sharp, data-forward, conversational",
        "format": "numbered thread, each tweet standalone but connected",
    },
    "email": {
        "name": "Email Snippet",
        "min_words": 150,
        "max_words": 200,
        "tone": "warm but professional, insertable into client comms",
        "format": "2-3 short paragraphs, no subject line needed",
    },
}

# ── Content calendar defaults ────────────────────────────────────────────────
CALENDAR_WEEKS = 3                # Default span for video content calendar
POSTS_PER_WEEK_LINKEDIN = 2      # LinkedIn posts per week
POSTS_PER_WEEK_TWITTER = 3       # X posts per week
NEWSLETTERS_PER_MONTH = 2        # Newsletter frequency
EMAILS_PER_WEEK = 1              # Client email snippets per week

# ── Compliance ───────────────────────────────────────────────────────────────
COMPLIANCE_AUTO_FLAGS = [
    "guaranteed", "guarantee", "risk-free", "no risk", "can't lose",
    "will outperform", "always beats", "superior returns",
    "best fund", "top performing", "never loses",
    "specific return", "projected returns", "expected returns",
    "% return", "annualized return",
]

COMPLIANCE_WARNING_PHRASES = [
    "past performance", "historical returns", "outperformed",
    "alpha generation", "beat the market", "excess returns",
]

# ── Content statuses ────────────────────────────────────────────────────────
STATUS_DRAFT = "draft"
STATUS_REVIEW = "review"
STATUS_APPROVED = "approved"
STATUS_SCHEDULED = "scheduled"
STATUS_PUBLISHED = "published"
STATUS_REJECTED = "rejected"

VALID_STATUSES = [
    STATUS_DRAFT, STATUS_REVIEW, STATUS_APPROVED,
    STATUS_SCHEDULED, STATUS_PUBLISHED, STATUS_REJECTED,
]
