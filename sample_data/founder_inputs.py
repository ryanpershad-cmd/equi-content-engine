"""
Sample founder inputs for Workflow 1 demos.
Three realistic inputs covering different formats and topics.
"""

VOICE_MEMO_PRIVATE_CREDIT = """So I was looking at the numbers this morning and it's striking — RIAs are sitting on 60/40 portfolios that had a 95% correlation between stocks and bonds in 2022. That's not diversification, that's just concentration with extra steps. The firms we're talking to, the $2 to $10 billion independent RIAs, they know this intuitively but they don't have the infrastructure to access institutional-quality hedge fund programs. That's literally what we built Equi to solve. The tender offer fund we're launching is going to be a game-changer because it gives RIAs a way to allocate their clients into a diversified hedge fund portfolio without the operational nightmare of managing five separate LP agreements and quarterly capital calls."""

BULLETS_MARKET_VOLATILITY = """- BlackRock just told investors to increase hedge fund allocations
- This validates what we've been saying for 2 years
- The difference: most RIAs can't access institutional hedge funds
- Equi's fund of funds solves the access + diligence + operations gap
- Our tender offer fund makes this even simpler — one allocation, full diversification
- Key stat: hedge fund industry saw $21B in net inflows Q1 2025"""

SLACK_RIA_TRENDS = """Just got back from the Titan Investors roundtable in DC. The energy around alternatives was palpable — every advisor I spoke to is thinking about how to add hedge fund exposure but they're all hitting the same wall: they don't have the team, the relationships, or the operational infrastructure to do it right. One CIO of a $4B firm literally said 'I know I need this but I don't know where to start.' That's our pitch in one sentence."""

# Metadata for demo scripts
SAMPLE_INPUTS = [
    {
        "id": "input_1",
        "text": VOICE_MEMO_PRIVATE_CREDIT,
        "founder": "itay",
        "label": "Voice Memo — 60/40 Correlation & Tender Offer Fund",
        "description": "Itay's voice memo about portfolio correlation breakdown and the tender offer fund launch",
    },
    {
        "id": "input_2",
        "text": BULLETS_MARKET_VOLATILITY,
        "founder": "tory",
        "label": "Bullet Points — BlackRock Validation & Industry Momentum",
        "description": "Tory's bullet points on BlackRock's hedge fund recommendation and industry inflows",
    },
    {
        "id": "input_3",
        "text": SLACK_RIA_TRENDS,
        "founder": "tory",
        "label": "Slack Message — Titan Investors Roundtable Recap",
        "description": "Tory's Slack message after attending the Titan Investors roundtable in DC",
    },
]
