#!/usr/bin/env python3
"""
Demo: Workflow 1 — Raw Founder Input → Multi-Platform Content

Processes 3 sample founder inputs (voice memo, bullets, Slack message)
and generates a full content package for each: LinkedIn post, newsletter
blurb, X/Twitter thread, and email snippet.

Runs without an API key (template fallbacks).
With ANTHROPIC_API_KEY set, uses Claude for generation.
"""
import sys
import json
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

import config
from db import get_connection, init_db, insert_batch, insert_piece, insert_compliance_log
from ingest.raw_input import parse_raw_input
from engine.tone_analyzer import analyze_tone
from engine.content_generator import generate_content_package
from review.compliance import review_content, format_compliance_report
from sample_data.founder_inputs import SAMPLE_INPUTS


def run_workflow1_demo():
    """Process all sample inputs and generate content packages."""
    print("=" * 70)
    print("  Equi Content Engine — Workflow 1 Demo")
    print("  Raw Founder Input → Multi-Platform Content")
    print("=" * 70)

    # Initialize
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    init_db(conn)

    all_packages = []

    for sample in SAMPLE_INPUTS:
        print(f"\n{'─' * 70}")
        print(f"  Processing: {sample['label']}")
        print(f"  Founder: {sample['founder'].title()}")
        print(f"{'─' * 70}")

        # Step 1: Parse raw input
        print("\n  ① Parsing raw input...")
        parsed = parse_raw_input(sample["text"], founder=sample["founder"])
        print(f"     Type detected: {parsed.input_type}")
        print(f"     Key points: {len(parsed.key_points)}")
        print(f"     Stats found: {parsed.stats_mentioned}")
        print(f"     Products referenced: {parsed.products_referenced}")
        print(f"     Urgency: {parsed.estimated_urgency}")

        # Step 2: Analyze tone
        print("\n  ② Analyzing tone & context...")
        analysis = analyze_tone(sample["text"], founder=sample["founder"])
        print(f"     Primary topic: {analysis.primary_topic}")
        print(f"     Sentiment: {analysis.sentiment}")
        print(f"     Data density: {analysis.data_density}")
        print(f"     Recommended angle: {analysis.recommended_angle}")

        # Step 3: Generate content
        print("\n  ③ Generating multi-platform content...")
        package = generate_content_package(parsed, analysis)
        print(f"     Method: {package.generation_method}")
        print(f"     LinkedIn: {len(package.linkedin.split())} words")
        print(f"     Newsletter: {len(package.newsletter.split())} words")
        print(f"     Twitter: {len(package.twitter_thread)} tweets")
        print(f"     Email: {len(package.email_snippet.split())} words")

        # Step 4: Compliance review
        print("\n  ④ Running compliance review...")
        compliance_results = {}
        platforms = {
            "linkedin": package.linkedin,
            "newsletter": package.newsletter,
            "email": package.email_snippet,
        }
        # Also check twitter thread as combined text
        platforms["twitter"] = "\n".join(package.twitter_thread)

        all_passed = True
        for platform, text in platforms.items():
            result = review_content(text, platform=platform)
            compliance_results[platform] = result
            status_icon = "✅" if result.passed else "❌"
            warnings = f" ({len(result.warnings)} warnings)" if result.warnings else ""
            print(f"     {platform.title()}: {status_icon}{warnings}")
            if not result.passed:
                all_passed = False

        # Step 5: Save to database
        print("\n  ⑤ Saving to database...")
        batch_id = insert_batch(
            conn, workflow="quick", founder=sample["founder"],
            source_summary=sample["label"], piece_count=4,
        )

        status = "review" if all_passed else "draft"
        db_pieces = []

        piece_id = insert_piece(
            conn, workflow="quick", source_type=parsed.input_type,
            source_text=sample["text"], founder=sample["founder"],
            platform="linkedin", content_type="post",
            title=f"LinkedIn: {analysis.primary_topic}",
            body=package.linkedin, status=status,
        )
        db_pieces.append(("linkedin", piece_id))

        piece_id = insert_piece(
            conn, workflow="quick", source_type=parsed.input_type,
            source_text=sample["text"], founder=sample["founder"],
            platform="newsletter", content_type="blurb",
            title=f"Newsletter: {analysis.primary_topic}",
            body=package.newsletter, status=status,
        )
        db_pieces.append(("newsletter", piece_id))

        piece_id = insert_piece(
            conn, workflow="quick", source_type=parsed.input_type,
            source_text=sample["text"], founder=sample["founder"],
            platform="twitter", content_type="thread",
            title=f"X Thread: {analysis.primary_topic}",
            body="\n\n".join(f"{i+1}/ {t}" for i, t in enumerate(package.twitter_thread)),
            status=status,
        )
        db_pieces.append(("twitter", piece_id))

        piece_id = insert_piece(
            conn, workflow="quick", source_type=parsed.input_type,
            source_text=sample["text"], founder=sample["founder"],
            platform="email", content_type="snippet",
            title=f"Email: {analysis.primary_topic}",
            body=package.email_snippet, status=status,
        )
        db_pieces.append(("email", piece_id))

        # Log compliance results
        for platform, pid in db_pieces:
            cr = compliance_results.get(platform)
            if cr:
                flags = [f["phrase"] for f in cr.flags] + [f["phrase"] for f in cr.warnings]
                insert_compliance_log(
                    conn, pid, action="auto_review",
                    notes=cr.review_notes, flags=flags if flags else None,
                )

        print(f"     Batch #{batch_id} created with {len(db_pieces)} pieces (status: {status})")

        all_packages.append({
            "input": sample,
            "analysis": {
                "topic": analysis.primary_topic,
                "sentiment": analysis.sentiment,
                "angle": analysis.recommended_angle,
            },
            "content": {
                "linkedin": package.linkedin,
                "newsletter": package.newsletter,
                "twitter_thread": package.twitter_thread,
                "email": package.email_snippet,
            },
            "compliance": {
                p: {"passed": r.passed, "flags": len(r.flags), "warnings": len(r.warnings)}
                for p, r in compliance_results.items()
            },
            "method": package.generation_method,
        })

    # Step 6: Write output files
    print(f"\n{'=' * 70}")
    print("  Writing output files...")

    # Full JSON output
    json_path = config.OUTPUT_DIR / "workflow1_output.json"
    json_path.write_text(json.dumps(all_packages, indent=2))
    print(f"  → {json_path}")

    # Markdown output (human-readable)
    md_path = config.OUTPUT_DIR / "workflow1_output.md"
    md_content = _format_markdown_output(all_packages)
    md_path.write_text(md_content)
    print(f"  → {md_path}")

    # Individual compliance reports
    for i, sample in enumerate(SAMPLE_INPUTS):
        pkg = all_packages[i]
        for platform in ["linkedin", "newsletter", "twitter", "email"]:
            text = pkg["content"].get(platform, "")
            if isinstance(text, list):
                text = "\n".join(text)
            cr = review_content(text, platform=platform)
            report = format_compliance_report(cr)
            report_path = config.OUTPUT_DIR / f"compliance_{sample['id']}_{platform}.txt"
            report_path.write_text(report)

    print(f"  → Compliance reports written")

    conn.close()

    print(f"\n{'=' * 70}")
    print(f"  ✅ Workflow 1 complete — {len(all_packages)} content packages generated")
    print(f"  Output: {config.OUTPUT_DIR}/")
    print(f"{'=' * 70}\n")

    return all_packages


def _format_markdown_output(packages: list[dict]) -> str:
    """Format all packages as a readable markdown document."""
    lines = ["# Equi Content Engine — Workflow 1 Output\n"]
    lines.append("*Raw Founder Input → Multi-Platform Content*\n")
    lines.append("---\n")

    for i, pkg in enumerate(packages, 1):
        inp = pkg["input"]
        lines.append(f"## {i}. {inp['label']}\n")
        lines.append(f"**Founder:** {inp['founder'].title()} | "
                      f"**Topic:** {pkg['analysis']['topic']} | "
                      f"**Method:** {pkg['method']}\n")
        lines.append(f"**Angle:** {pkg['analysis']['angle']}\n")

        # Source
        lines.append(f"### Source Input\n")
        lines.append(f"```\n{inp['text'][:500]}{'...' if len(inp['text']) > 500 else ''}\n```\n")

        # LinkedIn
        lines.append("### LinkedIn Post\n")
        lines.append(pkg["content"]["linkedin"] + "\n")

        # Newsletter
        lines.append("### Newsletter Blurb\n")
        lines.append(pkg["content"]["newsletter"] + "\n")

        # Twitter
        lines.append("### X/Twitter Thread\n")
        for j, tweet in enumerate(pkg["content"]["twitter_thread"], 1):
            lines.append(f"**{j}/** {tweet}\n")
        lines.append("")

        # Email
        lines.append("### Email Snippet\n")
        lines.append(pkg["content"]["email"] + "\n")

        # Compliance
        lines.append("### Compliance Review\n")
        for platform, result in pkg["compliance"].items():
            icon = "✅" if result["passed"] else "❌"
            extra = ""
            if result["warnings"]:
                extra = f" ({result['warnings']} warnings)"
            lines.append(f"- {platform.title()}: {icon}{extra}")
        lines.append("\n---\n")

    return "\n".join(lines)


if __name__ == "__main__":
    run_workflow1_demo()
