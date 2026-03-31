"""
Segment extractor — identifies key moments, quotes, and themes from video transcripts.
Works alongside video_processor for deeper content extraction.
"""
import re
from dataclasses import dataclass, field
from ingest.video_processor import ProcessedVideo, TranscriptSegment


@dataclass
class ExtractedSegment:
    """A thematically grouped segment for content creation."""
    theme: str
    summary: str
    key_quotes: list[str] = field(default_factory=list)
    data_points: list[str] = field(default_factory=list)
    segments: list[TranscriptSegment] = field(default_factory=list)
    recommended_platforms: list[str] = field(default_factory=list)
    content_angle: str = ""


def extract_themed_segments(video: ProcessedVideo) -> list[ExtractedSegment]:
    """
    Group transcript segments by theme and extract content-ready material.

    Returns segments organized by topic with quotes, data, and platform recommendations.
    """
    theme_keywords = {
        "The Correlation Problem": {
            "keywords": ["correlation", "60/40", "stocks and bonds", "diversification"],
            "angle": "Why traditional diversification is failing advisors",
            "platforms": ["linkedin", "twitter", "blog"],
        },
        "The Access Gap": {
            "keywords": ["access", "infrastructure", "can't access", "don't have"],
            "angle": "What's stopping RIAs from adding institutional alternatives",
            "platforms": ["linkedin", "newsletter", "email"],
        },
        "Industry Momentum": {
            "keywords": ["inflows", "blackrock", "momentum", "institutional"],
            "angle": "Smart money is moving to alternatives — the data is clear",
            "platforms": ["twitter", "linkedin", "newsletter"],
        },
        "The Equi Solution": {
            "keywords": ["tender offer", "fund of funds", "one allocation", "equi"],
            "angle": "How one vehicle can solve the alternatives access problem",
            "platforms": ["email", "newsletter", "linkedin"],
        },
        "Manager Selection & Diligence": {
            "keywords": ["diligence", "manager", "underwriting", "selection", "track record"],
            "angle": "Why manager selection in alternatives requires specialized expertise",
            "platforms": ["blog", "linkedin"],
        },
        "Portfolio Construction": {
            "keywords": ["portfolio", "construction", "uncorrelated", "risk-adjusted", "alpha"],
            "angle": "Building an alternatives sleeve that actually improves risk-adjusted returns",
            "platforms": ["blog", "linkedin", "newsletter"],
        },
    }

    extracted = []
    for theme_name, theme_def in theme_keywords.items():
        matching_segments = []
        for seg in video.segments:
            lower = seg.text.lower()
            if any(kw in lower for kw in theme_def["keywords"]):
                matching_segments.append(seg)

        if not matching_segments:
            continue

        # Extract quotes and data from matching segments
        quotes = []
        data_points = []
        for seg in matching_segments:
            # Find quotable sentences
            sentences = re.split(r'(?<=[.!?])\s+', seg.text)
            for sent in sentences:
                words = sent.split()
                if 8 <= len(words) <= 35:
                    quotes.append(f'"{sent.strip()}" — {seg.speaker}')
                # Check for data points
                if re.search(r'\d+\.?\d*\s*%|\$[\d,.]+', sent):
                    data_points.append(sent.strip())

        extracted.append(ExtractedSegment(
            theme=theme_name,
            summary=_summarize_segments(matching_segments),
            key_quotes=quotes[:5],
            data_points=data_points[:3],
            segments=matching_segments,
            recommended_platforms=theme_def["platforms"],
            content_angle=theme_def["angle"],
        ))

    return extracted


def _summarize_segments(segments: list[TranscriptSegment]) -> str:
    """Create a brief summary from a list of segments."""
    all_text = " ".join(s.text for s in segments)
    sentences = re.split(r'(?<=[.!?])\s+', all_text)

    # Pick the most substantive sentences (by length, presence of data)
    scored = []
    for sent in sentences:
        score = len(sent.split())
        if re.search(r'\d+', sent):
            score += 10
        scored.append((score, sent))

    scored.sort(reverse=True)
    top = [s[1] for s in scored[:3]]
    return " ".join(top)


def extract_social_quotes(video: ProcessedVideo, max_quotes: int = 10) -> list[dict]:
    """
    Extract social-media-ready quotes from a processed video.

    Returns dicts with quote, speaker, timestamp, and suggested platform.
    """
    results = []
    for seg in video.segments:
        sentences = re.split(r'(?<=[.!?])\s+', seg.text)
        for sent in sentences:
            words = sent.split()
            # Sweet spot for social: 10-30 words
            if not (10 <= len(words) <= 30):
                continue

            # Score for quotability
            score = 0
            lower = sent.lower()
            if re.search(r'\d+', sent):
                score += 3  # Has data
            if any(w in lower for w in ["game-changer", "critical", "key", "opportunity", "the real"]):
                score += 2  # Has punch
            if "?" in sent:
                score += 1  # Questions engage

            if score >= 2:
                platform = "twitter" if len(words) <= 20 else "linkedin"
                results.append({
                    "quote": sent.strip(),
                    "speaker": seg.speaker,
                    "timestamp": seg.start_time,
                    "platform": platform,
                    "score": score,
                })

            if len(results) >= max_quotes:
                break

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_quotes]
