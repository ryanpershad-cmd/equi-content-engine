"""
Blog writer — generates long-form blog posts from video segments and quotes.
Claude API with template fallback.
"""
import textwrap
import config
from ingest.video_processor import ProcessedVideo
from engine.segment_extractor import ExtractedSegment

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def generate_blog_post(video: ProcessedVideo,
                       themed_segments: list[ExtractedSegment]) -> str:
    """
    Generate a blog post (800-1200 words) from video content.

    Tries Claude first, falls back to template.
    """
    result = _generate_blog_claude(video, themed_segments)
    if result:
        return result
    return _generate_blog_template(video, themed_segments)


def _generate_blog_claude(video: ProcessedVideo,
                          themed_segments: list[ExtractedSegment]) -> str | None:
    """Generate blog post via Claude API."""
    if not HAS_ANTHROPIC or not config.ANTHROPIC_API_KEY:
        return None

    # Build context from segments
    segment_context = ""
    for seg in themed_segments:
        segment_context += f"\n## {seg.theme}\n"
        segment_context += f"Angle: {seg.content_angle}\n"
        for q in seg.key_quotes[:2]:
            segment_context += f"Quote: {q}\n"
        for d in seg.data_points[:2]:
            segment_context += f"Data: {d}\n"

    system = textwrap.dedent(f"""\
        You are the editorial team at {config.COMPANY_NAME}. Write in the combined voice
        of the founders — analytical yet accessible. The company helps independent RIAs
        access institutional-quality alternatives.

        {config.BRAND_VOICE}

        Products: {', '.join(config.PRODUCTS.values())}
    """)

    prompt = textwrap.dedent(f"""\
        Write a blog post (800-1200 words) based on a video conversation between
        {', '.join(video.speakers)} titled "{video.title}".

        Key themes and quotes from the conversation:
        {segment_context}

        Topics covered: {', '.join(video.topics_covered)}

        Format:
        - Title (use # heading)
        - Subtitle/hook
        - 4-6 sections with subheadings
        - Include direct quotes from the speakers
        - End with a forward-looking conclusion and soft CTA
        - Tone: thought leadership, not salesy
        - Reference specific data points where available

        Write the blog post directly — no meta-commentary.
    """)

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CONTENT_MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        print(f"  ⚠ Claude API error (blog): {e}")
        return None


def _generate_blog_template(video: ProcessedVideo,
                            themed_segments: list[ExtractedSegment]) -> str:
    """Template-based blog post generation."""
    title = video.title or "The Case for Alternatives in RIA Portfolios"
    speakers_str = " and ".join(video.speakers)

    sections = []

    # Title and intro
    sections.append(f"# {title}\n")
    sections.append(
        f"*A conversation between {speakers_str} — {config.COMPANY_NAME}*\n"
    )
    sections.append(
        f"The alternatives landscape is at an inflection point. In a recent conversation, "
        f"{speakers_str} sat down to discuss what's driving the shift toward hedge fund "
        f"allocations in RIA portfolios — and why the next 12 months matter more than the last decade.\n"
    )

    # Generate sections from themed segments
    for seg in themed_segments[:5]:
        section = f"## {seg.theme}\n\n"

        if seg.content_angle:
            section += f"{seg.content_angle}.\n\n"

        # Include quotes
        for quote in seg.key_quotes[:2]:
            section += f"> {quote}\n\n"

        # Include data points
        if seg.data_points:
            section += "The data reinforces this view: "
            section += ". ".join(seg.data_points[:2]) + ".\n\n"

        # Add connecting narrative
        section += _get_section_narrative(seg.theme)
        sections.append(section)

    # If we don't have enough themed segments, add default sections
    if len(themed_segments) < 3:
        sections.append(
            "## Why RIAs Are Underallocated\n\n"
            "The typical independent RIA allocates less than 5% to alternatives — compared to "
            "20-40% for institutional investors like endowments and pensions. This isn't because "
            "advisors don't understand the value. It's because they lack the infrastructure: the "
            "manager relationships, the operational capabilities, and the diligence resources "
            "that institutional allocators take for granted.\n"
        )
        sections.append(
            "## A New Approach\n\n"
            f"{config.COMPANY_NAME} was built to close this gap. By combining deep alternatives "
            f"expertise with modern technology, the platform gives RIAs a single point of access "
            f"to diversified, institutional-quality alternative strategies — without the "
            f"operational complexity of building it in-house.\n"
        )

    # Conclusion
    sections.append(
        "## Looking Ahead\n\n"
        "The shift toward alternatives in advisor portfolios isn't a trend — it's a structural "
        "reallocation that's just beginning. The advisors who build this capability now will have "
        "a meaningful advantage in serving their clients over the next decade.\n\n"
        f"*To learn more about how {config.COMPANY_NAME} helps RIAs access institutional alternatives, "
        f"visit [{config.WEBSITE}]({config.WEBSITE}).*"
    )

    return "\n".join(sections)


def _get_section_narrative(theme: str) -> str:
    """Get connecting narrative text for a theme section."""
    narratives = {
        "The Correlation Problem": (
            "For decades, the 60/40 portfolio was the bedrock of financial planning. "
            "But when stocks and bonds move in lockstep — as they did throughout 2022 — "
            "the entire premise of that allocation breaks down. Advisors need true "
            "diversification, and that means looking beyond traditional asset classes.\n"
        ),
        "The Access Gap": (
            "The irony is that the firms best positioned to benefit from alternatives "
            "are often the least equipped to access them. Independent RIAs managing "
            "$2B to $10B have sophisticated clients with institutional expectations, "
            "but they lack the institutional infrastructure to deliver.\n"
        ),
        "Industry Momentum": (
            "The institutional community has been increasing alternatives allocations "
            "for years. What's new is that this consensus is now reaching the independent "
            "advisor channel — and the infrastructure is finally catching up to enable it.\n"
        ),
        "The Equi Solution": (
            f"{config.COMPANY_NAME}'s approach is fundamentally different from the traditional "
            f"fund-of-funds model. By combining technology-driven diligence, operational "
            f"infrastructure, and curated manager access, the platform turns what used to be "
            f"a multi-month, multi-vendor project into a single allocation decision.\n"
        ),
        "Manager Selection & Diligence": (
            "In alternatives, manager selection isn't just important — it's everything. "
            "The dispersion between top-quartile and bottom-quartile hedge fund managers "
            "is significantly wider than in traditional asset classes. Getting the diligence "
            "right is the difference between portfolio enhancement and portfolio drag.\n"
        ),
        "Portfolio Construction": (
            "The goal isn't just to add alternatives — it's to add them in a way that "
            "genuinely improves the portfolio's risk-adjusted return profile. That requires "
            "careful attention to correlations, strategy diversification, and liquidity management.\n"
        ),
    }
    return narratives.get(theme, "")
