"""
Content generator — Claude API with template fallbacks.
Generates multi-platform content from parsed input + tone analysis.
"""
import re
import textwrap
from dataclasses import dataclass, field

import config
from ingest.raw_input import ParsedInput
from engine.tone_analyzer import ToneAnalysis

# Try to import anthropic; graceful fallback
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class ContentPackage:
    """Complete multi-platform content package from a single input."""
    source_input: str
    founder: str
    tone_analysis: ToneAnalysis
    linkedin: str = ""
    newsletter: str = ""
    twitter_thread: list[str] = field(default_factory=list)
    email_snippet: str = ""
    generation_method: str = "template"  # "claude" or "template"


# ── Claude API generation ────────────────────────────────────────────────────

def _build_system_prompt(founder: str) -> str:
    """System prompt for Claude content generation."""
    founder_info = config.FOUNDERS.get(founder, config.FOUNDERS["tory"])
    return textwrap.dedent(f"""\
        You are a content writer for {config.COMPANY_NAME}, an alternatives infrastructure
        platform for independent RIAs. You write in the voice of {founder_info['name']}
        ({founder_info['full_title']}).

        Company: {config.COMPANY_DESCRIPTION}

        Brand voice: {config.BRAND_VOICE}

        Writing style for {founder_info['name']}: {founder_info['voice']}

        Products:
        - {config.PRODUCTS['custom_fof']}
        - {config.PRODUCTS['branded_funds']}
        - {config.PRODUCTS['tender_offer']}

        Important rules:
        1. Never make specific return promises or guarantees
        2. Use "may", "seeks to", "designed to" for forward-looking statements
        3. Reference data points from the source material accurately
        4. Position {config.COMPANY_NAME} as a thought leader, not a salesperson
        5. Every piece should provide genuine insight, not just promote
        6. Use {config.COMPANY_TAGLINE} sparingly — it's a tagline, not a crutch
    """)


def _call_claude(prompt: str, system: str, max_tokens: int = 4096) -> str | None:
    """Call Claude API. Returns None if unavailable."""
    if not HAS_ANTHROPIC or not config.ANTHROPIC_API_KEY:
        return None
    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"  ⚠ Claude API error: {e}")
        return None


def generate_content_package(parsed: ParsedInput, analysis: ToneAnalysis) -> ContentPackage:
    """
    Generate a full content package for all platforms.

    Tries Claude API first, falls back to templates if unavailable.
    """
    package = ContentPackage(
        source_input=parsed.raw_text,
        founder=parsed.founder,
        tone_analysis=analysis,
    )

    system = _build_system_prompt(parsed.founder)

    # Try Claude for each platform
    linkedin = _generate_linkedin_claude(parsed, analysis, system)
    newsletter = _generate_newsletter_claude(parsed, analysis, system)
    twitter = _generate_twitter_claude(parsed, analysis, system)
    email = _generate_email_claude(parsed, analysis, system)

    if linkedin:
        package.linkedin = linkedin
        package.newsletter = newsletter or _generate_newsletter_template(parsed, analysis)
        package.twitter_thread = twitter or _generate_twitter_template(parsed, analysis)
        package.email_snippet = email or _generate_email_template(parsed, analysis)
        package.generation_method = "claude"
    else:
        # Full template fallback
        package.linkedin = _generate_linkedin_template(parsed, analysis)
        package.newsletter = _generate_newsletter_template(parsed, analysis)
        package.twitter_thread = _generate_twitter_template(parsed, analysis)
        package.email_snippet = _generate_email_template(parsed, analysis)
        package.generation_method = "template"

    return package


# ── Claude generation per platform ──────────────────────────────────────────

def _generate_linkedin_claude(parsed: ParsedInput, analysis: ToneAnalysis, system: str) -> str | None:
    prompt = textwrap.dedent(f"""\
        Write a LinkedIn post (500-800 words) based on this raw input from the founder:

        ---
        {parsed.raw_text}
        ---

        Topic: {analysis.primary_topic}
        Angle: {analysis.recommended_angle}
        Key data points: {', '.join(parsed.stats_mentioned) or 'none specified'}
        Products to reference: {', '.join(parsed.products_referenced) or 'none specified'}

        Format: Professional thought leadership. Use paragraph breaks for readability.
        End with 3-5 relevant hashtags from: {', '.join(analysis.suggested_hashtags)}
        Include a subtle CTA (learn more, connect, comment).

        Write the post directly — no meta-commentary, no "Here's a LinkedIn post:".
    """)
    return _call_claude(prompt, system)


def _generate_newsletter_claude(parsed: ParsedInput, analysis: ToneAnalysis, system: str) -> str | None:
    prompt = textwrap.dedent(f"""\
        Write a newsletter blurb (200-300 words) based on this raw input:

        ---
        {parsed.raw_text}
        ---

        Topic: {analysis.primary_topic}
        Angle: {analysis.recommended_angle}

        Format: Punchy, informative. Bold key stats. Include a clear CTA at the end
        (e.g., "Schedule a call", "Download our guide", "Reply to this email").
        Short paragraphs. Hook the reader in the first sentence.

        Write the blurb directly — no meta-commentary.
    """)
    return _call_claude(prompt, system, max_tokens=1024)


def _generate_twitter_claude(parsed: ParsedInput, analysis: ToneAnalysis, system: str) -> list[str] | None:
    prompt = textwrap.dedent(f"""\
        Write an X/Twitter thread (5-7 tweets, each UNDER 280 characters) based on this input:

        ---
        {parsed.raw_text}
        ---

        Topic: {analysis.primary_topic}
        Key stats: {', '.join(parsed.stats_mentioned) or 'none specified'}

        Format each tweet on its own line, numbered 1/, 2/, etc.
        First tweet should hook. Last tweet should CTA or tag @join_equi.
        Be concise, data-forward, conversational. No hashtags mid-thread (save for last tweet).

        Write the thread directly — no meta-commentary.
    """)
    result = _call_claude(prompt, system, max_tokens=1024)
    if result:
        # Parse numbered tweets
        tweets = []
        for line in result.strip().split("\n"):
            line = line.strip()
            if line and re.match(r'^\d+[/.)]\s*', line):
                tweet = re.sub(r'^\d+[/.)]\s*', '', line).strip()
                if tweet:
                    tweets.append(tweet)
        return tweets if tweets else None
    return None


def _generate_email_claude(parsed: ParsedInput, analysis: ToneAnalysis, system: str) -> str | None:
    prompt = textwrap.dedent(f"""\
        Write an email snippet (150-200 words) that can be inserted into client communications.
        Based on this input:

        ---
        {parsed.raw_text}
        ---

        Topic: {analysis.primary_topic}
        Tone: Warm but professional. This goes directly to advisors/clients.
        Format: 2-3 short paragraphs. No subject line. No greeting. Just the insertable body.

        Write the snippet directly — no meta-commentary.
    """)
    return _call_claude(prompt, system, max_tokens=1024)


# ── Template fallbacks ──────────────────────────────────────────────────────

def _generate_linkedin_template(parsed: ParsedInput, analysis: ToneAnalysis) -> str:
    """Template-based LinkedIn post generation (500-800 words)."""
    founder_info = config.FOUNDERS.get(parsed.founder, config.FOUNDERS["tory"])
    hook = analysis.hook_suggestions[0] if analysis.hook_suggestions else "The alternatives landscape is shifting."

    body_paragraphs = []

    # ── Opening hook (punchy, stops the scroll) ─────────────────────────────
    body_paragraphs.append(hook)
    body_paragraphs.append(
        "Let that sink in for a moment. Because the implications for how we construct "
        "portfolios — and how we serve clients — are significant. Every week, I talk "
        "to advisors who are grappling with this exact challenge, and the conversation "
        "always lands in the same place."
    )

    # ── Market context paragraph ────────────────────────────────────────────
    if analysis.market_context:
        body_paragraphs.append(
            f"We're in a {analysis.market_context} environment, and what we're hearing from "
            f"the independent RIAs we work with — firms managing $2B to $15B — is consistent: "
            f"the old playbook isn't working anymore. The assumptions that guided portfolio "
            f"construction for the last two decades are breaking down in real time, and the "
            f"advisors who recognize this first will have a structural advantage."
        )
    else:
        body_paragraphs.append(
            "The market environment has shifted. Interest rate dynamics, correlation regimes, "
            "and client expectations have all changed — and portfolio construction needs to "
            "evolve with them. The advisors who adapt first will serve their clients best."
        )

    # ── Key points (adapted by input type) ──────────────────────────────────
    if parsed.input_type == "bullets":
        for i, point in enumerate(parsed.key_points[:5]):
            if i == 0:
                body_paragraphs.append(
                    f"{point}\n\nThis isn't a fringe view — it's rapidly becoming consensus "
                    f"across the institutional community. And when the largest allocators in "
                    f"the world start moving in a direction, independent advisors need to pay attention."
                )
            elif parsed.stats_mentioned and i == 1:
                body_paragraphs.append(
                    f"The numbers tell the story: {parsed.stats_mentioned[0]}. "
                    f"{point} For years, alternatives were considered a 'nice to have' for "
                    f"advisor portfolios. That framing is outdated. They're now a critical "
                    f"component of any serious portfolio construction effort."
                )
            elif i == 2:
                body_paragraphs.append(
                    f"{point}\n\nI hear this from advisors every week. The desire to allocate "
                    f"is there — what's missing is the infrastructure, the diligence capability, "
                    f"and the operational support to execute it at scale."
                )
            else:
                body_paragraphs.append(point)
    else:
        # For prose-based inputs, use the key points with expanded commentary
        for i, point in enumerate(parsed.key_points[:4]):
            if len(point.split()) > 12:
                if i == 0:
                    body_paragraphs.append(
                        f"{point}\n\nThis is a pattern we're seeing across the industry. "
                        f"The independent RIA channel — firms with $1B to $30B in AUM — "
                        f"is at an inflection point. Client expectations are rising, "
                        f"competitive pressure from wirehouses and multi-family offices is "
                        f"intensifying, and the traditional portfolio toolkit isn't cutting it "
                        f"anymore."
                    )
                elif i == 1:
                    body_paragraphs.append(
                        f"{point}\n\nAnd this isn't just about performance. It's about risk "
                        f"management, it's about genuine diversification, and it's about "
                        f"meeting the increasingly sophisticated expectations of high-net-worth "
                        f"clients who know what institutional portfolios look like."
                    )
                elif i == 2:
                    body_paragraphs.append(
                        f"{point}\n\nThe firms that figure this out first won't just retain "
                        f"their existing clients — they'll attract new ones. Because in a world "
                        f"where every advisor has access to the same ETFs and model portfolios, "
                        f"alternatives capability is a genuine differentiator."
                    )
                else:
                    body_paragraphs.append(point)

    # ── Institutional context expansion ────────────────────────────────────
    body_paragraphs.append(
        "Here's the institutional reality: endowments like Yale and Stanford have allocated "
        "25-40% to alternatives for two decades, generating meaningfully higher risk-adjusted "
        "returns than traditional 60/40 benchmarks. Pensions and sovereign wealth funds "
        "have followed the same playbook. Yet the average independent RIA allocates less than "
        "5% to alternatives. That gap represents both a risk to client portfolios and an "
        "enormous opportunity for advisors who close it."
    )

    # ── Industry context / social proof ─────────────────────────────────────
    if parsed.companies_mentioned:
        companies = ", ".join(parsed.companies_mentioned[:3])
        body_paragraphs.append(
            f"It's worth noting that firms like {companies} are actively increasing their "
            f"focus on alternative allocations for the wealth channel. The direction of travel "
            f"is clear — and the question for independent advisors isn't whether to allocate, "
            f"but how to do it with institutional rigor."
        )

    if parsed.events_mentioned:
        events = ", ".join(parsed.events_mentioned[:2])
        body_paragraphs.append(
            f"Having recently attended {events}, the energy around this topic is palpable. "
            f"Every conversation comes back to the same theme: advisors want alternatives "
            f"exposure, but they need a partner who understands both the investment complexity "
            f"and the operational reality of running an RIA."
        )

    # ── Product reference / Equi's role ─────────────────────────────────────
    if parsed.products_referenced:
        products = " and ".join(parsed.products_referenced[:2])
        body_paragraphs.append(
            f"This is exactly why we built {config.COMPANY_NAME}'s {products}. "
            f"We wanted to eliminate the three biggest barriers RIAs face when accessing "
            f"alternatives: the access gap (institutional minimums are too high), the "
            f"diligence gap (evaluating hedge fund managers requires specialized expertise), "
            f"and the operations gap (managing LP agreements, capital calls, and reporting "
            f"across multiple funds is an operational nightmare).\n\n"
            f"One allocation. Full diversification. Institutional-quality diligence. "
            f"Professional operations. That's the model."
        )
    else:
        body_paragraphs.append(
            f"At {config.COMPANY_NAME}, we've spent years building the infrastructure that "
            f"solves this problem. {config.COMPANY_TAGLINE} — because advisors deserve "
            f"institutional-quality alternatives access without building it from scratch.\n\n"
            f"We handle the diligence, the manager selection, the operational complexity, "
            f"and the ongoing monitoring — so advisors can focus on what they do best: "
            f"serving their clients."
        )

    # ── Forward-looking / call to action ────────────────────────────────────
    body_paragraphs.append(
        f"The question isn't whether alternatives belong in advisor portfolios — the data "
        f"has settled that debate. The question is whether advisors have the right partner "
        f"and infrastructure to access them with institutional rigor.\n\n"
        f"The advisors who build this capability now will compound that advantage for years. "
        f"The ones who wait will spend the next three years building what they could have "
        f"accessed today."
    )

    body_paragraphs.append(
        f"What are you seeing in your practice? How are you thinking about alternatives "
        f"allocations for your clients? I'd love to hear — drop a comment or send me a message.\n\n"
        + " ".join(analysis.suggested_hashtags[:5])
    )

    return "\n\n".join(body_paragraphs)


def _generate_newsletter_template(parsed: ParsedInput, analysis: ToneAnalysis) -> str:
    """Template-based newsletter blurb (200-300 words)."""
    hook = analysis.hook_suggestions[0] if analysis.hook_suggestions else "Here's what we're watching."
    founder_info = config.FOUNDERS.get(parsed.founder, config.FOUNDERS["tory"])

    parts = []

    parts.append(f"**{analysis.primary_topic}**\n")
    parts.append(f"{hook}\n")

    # Stats + context paragraph
    if parsed.stats_mentioned:
        parts.append(
            f"**The data is striking:** {parsed.stats_mentioned[0]}. "
            f"This is the kind of structural shift that separates advisors who are "
            f"positioned for the next decade from those still running yesterday's playbook."
        )

    # Core insight from the founder
    if parsed.key_points:
        # Use the most substantive point
        best_point = max(parsed.key_points[:3], key=lambda p: len(p.split()))
        parts.append(
            f'As our {founder_info["title"]} {founder_info["name"]} puts it: "{best_point}"'
        )

    # Product tie-in
    if parsed.products_referenced:
        products = parsed.products_referenced[0]
        parts.append(
            f"This is precisely the challenge {config.COMPANY_NAME}'s {products} was built "
            f"to address. One allocation gives advisors diversified, institutional-quality "
            f"access to alternatives — without the operational complexity of managing "
            f"multiple fund relationships, LP agreements, and capital calls."
        )
    else:
        parts.append(
            f"{config.COMPANY_NAME} was purpose-built for this moment — giving independent "
            f"RIAs the same alternatives infrastructure that institutions take for granted, "
            f"without requiring a 20-person investment team to execute."
        )

    # Forward-looking + CTA
    parts.append(
        f"The advisors who move now will have a structural advantage. The ones who wait "
        f"will spend the next three years building what they could have accessed today.\n\n"
        f"**→ [Schedule a 15-minute call]({config.WEBSITE}) to learn how {config.COMPANY_NAME} "
        f"can help your practice access institutional alternatives.**"
    )

    return "\n\n".join(parts)


def _generate_twitter_template(parsed: ParsedInput, analysis: ToneAnalysis) -> list[str]:
    """Template-based Twitter/X thread."""
    tweets = []
    hook = analysis.hook_suggestions[0] if analysis.hook_suggestions else "Thread on what we're seeing in alternatives 🧵"

    # Tweet 1: Hook
    tweets.append(f"{hook} 🧵")

    # Tweet 2: Context/stat
    if parsed.stats_mentioned:
        tweets.append(f"The data: {parsed.stats_mentioned[0]}. This is not a blip — it's a structural shift.")
    else:
        tweets.append("The structural shift in advisor portfolios is accelerating. Here's what's driving it.")

    # Tweets 3-5: Key points (trimmed to 280 chars)
    for point in parsed.key_points[:3]:
        tweet = point.strip()
        if len(tweet) > 275:
            tweet = tweet[:272] + "..."
        tweets.append(tweet)

    # Tweet 6: Equi angle
    tweets.append(
        f"This is why @join_equi exists — institutional alternatives access for "
        f"independent RIAs. One allocation, full diversification."
    )

    # Tweet 7: CTA
    tweets.append(
        f"If you're an RIA thinking about alternatives, let's talk. "
        f"DM or visit {config.WEBSITE} @join_equi"
    )

    # Enforce 280 char limit
    tweets = [t[:280] for t in tweets]

    return tweets


def _generate_email_template(parsed: ParsedInput, analysis: ToneAnalysis) -> str:
    """Template-based email snippet (150-200 words)."""
    founder_info = config.FOUNDERS.get(parsed.founder, config.FOUNDERS["tory"])

    opening = ""
    if analysis.sentiment == "urgent":
        opening = (
            "We wanted to share a timely observation about the alternatives market "
            "that has direct implications for portfolio construction."
        )
    elif analysis.sentiment == "bullish":
        opening = (
            "There's meaningful momentum building in alternatives — and it matters "
            "for how advisors serve their clients going forward."
        )
    else:
        opening = (
            "We've been watching an important shift in how advisors approach portfolio "
            "construction, and wanted to share our perspective."
        )

    stat = ""
    if parsed.stats_mentioned:
        stat = f" The numbers are striking: {parsed.stats_mentioned[0]}."

    # Core insight — use the most compelling key point
    if parsed.key_points:
        insight = max(parsed.key_points[:3], key=lambda p: len(p.split()))
    else:
        insight = analysis.recommended_angle

    product_ref = ""
    if parsed.products_referenced:
        product_ref = (
            f" Our {parsed.products_referenced[0]} is specifically designed for firms "
            f"like yours — providing institutional-quality alternatives access through "
            f"a single, operationally simple allocation."
        )

    return (
        f"{opening}{stat}\n\n"
        f"{insight}\n\n"
        f"This is the core challenge we hear from advisors every day: the investment case "
        f"for alternatives is clear, but the infrastructure to execute is missing.{product_ref}\n\n"
        f"We'd welcome the chance to walk through how {config.COMPANY_NAME}'s "
        f"approach could complement your current allocation strategy. "
        f"Happy to set up a brief call at your convenience."
    )
