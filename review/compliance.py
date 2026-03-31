"""
Compliance review — automated flagging and approval workflow.
Checks content for SEC compliance issues before distribution.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import config


@dataclass
class ComplianceResult:
    """Result of a compliance review on a content piece."""
    piece_id: int | None = None
    passed: bool = True
    flags: list[dict] = field(default_factory=list)      # Hard flags — must fix
    warnings: list[dict] = field(default_factory=list)    # Soft flags — review recommended
    suggested_fixes: list[str] = field(default_factory=list)
    review_notes: str = ""
    reviewed_at: str = ""


def review_content(text: str, piece_id: int | None = None,
                   platform: str = "linkedin") -> ComplianceResult:
    """
    Run automated compliance review on content text.

    Checks for:
    1. Prohibited language (guarantees, promises)
    2. Warning phrases (performance references)
    3. Missing disclaimers on certain content types
    4. Platform-specific issues

    Args:
        text: Content text to review
        piece_id: Optional database piece ID
        platform: Target platform

    Returns:
        ComplianceResult with flags, warnings, and suggestions
    """
    result = ComplianceResult(
        piece_id=piece_id,
        reviewed_at=datetime.now(timezone.utc).isoformat(),
    )

    lower = text.lower()

    # ── Hard flags (must fix) ──────────────────────────────────────────────
    for phrase in config.COMPLIANCE_AUTO_FLAGS:
        if phrase in lower:
            idx = lower.index(phrase)
            context = text[max(0, idx - 30):idx + len(phrase) + 30]
            result.flags.append({
                "type": "prohibited_language",
                "phrase": phrase,
                "context": f"...{context}...",
                "severity": "high",
                "rule": "SEC Rule 206(4)-1 — no misleading statements",
            })
            result.suggested_fixes.append(
                f"Remove or rephrase '{phrase}'. Use 'seeks to', 'may', or "
                f"'is designed to' instead of absolute claims."
            )

    # ── Warning flags (review recommended) ─────────────────────────────────
    for phrase in config.COMPLIANCE_WARNING_PHRASES:
        if phrase in lower:
            idx = lower.index(phrase)
            context = text[max(0, idx - 30):idx + len(phrase) + 30]
            result.warnings.append({
                "type": "performance_reference",
                "phrase": phrase,
                "context": f"...{context}...",
                "severity": "medium",
                "rule": "Ensure proper context — past performance does not guarantee future results",
            })

    # ── Specific return claims ─────────────────────────────────────────────
    return_patterns = [
        r'\d+\.?\d*%\s*(?:return|gain|profit|yield)',
        r'(?:return|gain|profit|yield)\s*(?:of\s*)?\d+\.?\d*%',
        r'(?:generated|produced|delivered|achieved)\s+\d+\.?\d*%',
    ]
    for pattern in return_patterns:
        match = re.search(pattern, lower)
        if match:
            result.flags.append({
                "type": "specific_return_claim",
                "phrase": match.group(),
                "context": text[max(0, match.start() - 20):match.end() + 20],
                "severity": "high",
                "rule": "Avoid specific return claims. Reference industry/index data with attribution.",
            })
            result.suggested_fixes.append(
                "Replace specific return claims with properly attributed industry data "
                "or use forward-looking qualifiers."
            )

    # ── Missing disclaimer check (for longer content) ──────────────────────
    word_count = len(text.split())
    if word_count > 300 and platform in ("blog", "newsletter", "email"):
        disclaimer_phrases = [
            "not a guarantee", "past performance", "for informational purposes",
            "not investment advice", "consult", "sec-registered",
        ]
        has_disclaimer = any(dp in lower for dp in disclaimer_phrases)
        if not has_disclaimer:
            result.warnings.append({
                "type": "missing_disclaimer",
                "phrase": "",
                "context": "Long-form content without a disclaimer",
                "severity": "medium",
                "rule": "Long-form content distributed to clients should include appropriate disclaimers",
            })
            result.suggested_fixes.append(
                "Consider adding: 'This content is for informational purposes only "
                "and does not constitute investment advice.'"
            )

    # ── Competitor disparagement check ─────────────────────────────────────
    disparagement_patterns = [
        r'(?:unlike|better than|superior to)\s+(?:other|competing|rival)',
        r'(?:worst|terrible|awful|failing)\s+(?:fund|manager|strategy)',
    ]
    for pattern in disparagement_patterns:
        match = re.search(pattern, lower)
        if match:
            result.warnings.append({
                "type": "competitor_disparagement",
                "phrase": match.group(),
                "context": text[max(0, match.start() - 20):match.end() + 20],
                "severity": "medium",
                "rule": "Avoid disparaging competitors. Focus on Equi's differentiators positively.",
            })

    # ── Set passed/failed ──────────────────────────────────────────────────
    result.passed = len(result.flags) == 0

    # Build review notes
    if result.flags:
        result.review_notes = (
            f"BLOCKED: {len(result.flags)} compliance issue(s) found. "
            f"Content must be revised before publication."
        )
    elif result.warnings:
        result.review_notes = (
            f"PASSED WITH WARNINGS: {len(result.warnings)} item(s) flagged for review. "
            f"Content can proceed but should be reviewed by compliance."
        )
    else:
        result.review_notes = "PASSED: No compliance issues detected."

    return result


def get_compliance_summary(results: list[ComplianceResult]) -> dict:
    """Generate a summary of compliance results across multiple pieces."""
    total = len(results)
    passed = sum(1 for r in results if r.passed and not r.warnings)
    passed_with_warnings = sum(1 for r in results if r.passed and r.warnings)
    blocked = sum(1 for r in results if not r.passed)

    all_flag_types = {}
    for r in results:
        for flag in r.flags + r.warnings:
            t = flag["type"]
            all_flag_types[t] = all_flag_types.get(t, 0) + 1

    return {
        "total_reviewed": total,
        "passed_clean": passed,
        "passed_with_warnings": passed_with_warnings,
        "blocked": blocked,
        "flag_breakdown": all_flag_types,
    }


def format_compliance_report(result: ComplianceResult) -> str:
    """Format a single compliance result as readable text."""
    lines = []
    lines.append(f"Compliance Review — {'✅ PASSED' if result.passed else '❌ BLOCKED'}")
    lines.append(f"Reviewed: {result.reviewed_at}")
    lines.append("")

    if result.flags:
        lines.append(f"🚫 Issues ({len(result.flags)}):")
        for flag in result.flags:
            lines.append(f"  • [{flag['severity'].upper()}] {flag['type']}: \"{flag['phrase']}\"")
            lines.append(f"    Context: {flag['context']}")
            lines.append(f"    Rule: {flag['rule']}")
        lines.append("")

    if result.warnings:
        lines.append(f"⚠️  Warnings ({len(result.warnings)}):")
        for warn in result.warnings:
            lines.append(f"  • [{warn['severity'].upper()}] {warn['type']}: \"{warn['phrase']}\"")
            lines.append(f"    Context: {warn['context']}")
            lines.append(f"    Rule: {warn['rule']}")
        lines.append("")

    if result.suggested_fixes:
        lines.append("Suggested fixes:")
        for fix in result.suggested_fixes:
            lines.append(f"  → {fix}")
        lines.append("")

    lines.append(result.review_notes)
    return "\n".join(lines)
