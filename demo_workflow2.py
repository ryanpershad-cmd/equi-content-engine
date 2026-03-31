#!/usr/bin/env python3
"""
Demo: Workflow 2 — Long-Form Video → Content Library + Calendar

Processes a 30-minute video transcript (Itay & Tory discussing hedge fund
allocations) and produces:
- 5 clip suggestions with timestamps
- Full blog post (800-1200 words)
- 8-10 social media posts
- Email teaser
- 3-week content calendar (CSV + JSON)

Runs without an API key (template fallbacks).
With ANTHROPIC_API_KEY set, uses Claude for generation.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from db import get_connection, init_db, insert_batch, insert_piece, insert_calendar_entry, insert_compliance_log
from ingest.video_processor import process_transcript
from engine.tone_analyzer import analyze_tone
from engine.segment_extractor import extract_themed_segments, extract_social_quotes
from engine.content_generator import generate_content_package
from engine.blog_writer import generate_blog_post
from engine.calendar_builder import build_calendar, calendar_to_csv, save_calendar
from review.compliance import review_content, format_compliance_report
from ingest.raw_input import parse_raw_input
from sample_data.video_transcript import VIDEO_TRANSCRIPT, VIDEO_METADATA


def run_workflow2_demo():
    """Process sample video transcript and generate full content library."""
    print("=" * 70)
    print("  Equi Content Engine — Workflow 2 Demo")
    print("  Long-Form Video → Content Library + Calendar")
    print("=" * 70)

    # Initialize
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    init_db(conn)

    # ── Step 1: Process transcript ──────────────────────────────────────────
    print(f"\n{'─' * 70}")
    print(f"  Processing: {VIDEO_METADATA['title']}")
    print(f"  Speakers: {', '.join(VIDEO_METADATA['speakers'])}")
    print(f"  Duration: {VIDEO_METADATA['duration_minutes']} minutes")
    print(f"{'─' * 70}")

    print("\n  ① Processing transcript...")
    video = process_transcript(
        VIDEO_TRANSCRIPT,
        title=VIDEO_METADATA["title"],
        speakers=VIDEO_METADATA["speakers"],
        duration_minutes=VIDEO_METADATA["duration_minutes"],
    )
    print(f"     Segments parsed: {len(video.segments)}")
    print(f"     Total words: {video.total_words}")
    print(f"     Topics identified: {len(video.topics_covered)}")
    for topic in video.topics_covered:
        print(f"       • {topic}")

    # ── Step 2: Extract themed segments ─────────────────────────────────────
    print("\n  ② Extracting themed segments...")
    themed = extract_themed_segments(video)
    for seg in themed:
        print(f"     • {seg.theme}: {len(seg.key_quotes)} quotes, {len(seg.data_points)} data points")

    # ── Step 3: Generate clip suggestions ───────────────────────────────────
    print("\n  ③ Generating clip suggestions...")
    clips = video.clip_suggestions
    print(f"     Found {len(clips)} clip candidates:")
    for i, clip in enumerate(clips, 1):
        print(f"     {i}. [{clip.start_time} → {clip.end_time}] {clip.title}")
        print(f"        Key quote: {clip.key_quote[:80]}...")

    # ── Step 4: Generate blog post ──────────────────────────────────────────
    print("\n  ④ Generating blog post...")
    blog = generate_blog_post(video, themed)
    blog_words = len(blog.split())
    print(f"     Blog post: {blog_words} words")

    # ── Step 5: Generate social media posts ─────────────────────────────────
    print("\n  ⑤ Generating social media posts...")
    social_quotes = extract_social_quotes(video, max_quotes=10)
    print(f"     Extracted {len(social_quotes)} social-ready quotes")

    # Generate platform-specific posts from themed segments
    social_posts = []

    # LinkedIn posts from key themes
    for seg in themed[:3]:
        analysis = analyze_tone(
            " ".join(s.text for s in seg.segments),
            founder="itay",
        )
        # Create a mini-input from the segment
        parsed = parse_raw_input(
            " ".join(s.text for s in seg.segments),
            founder="itay",
        )
        pkg = generate_content_package(parsed, analysis)

        social_posts.append({
            "platform": "linkedin",
            "content_type": "post",
            "title": f"LinkedIn: {seg.theme}",
            "body": pkg.linkedin,
            "source": f"Video segment: {seg.theme}",
        })

        social_posts.append({
            "platform": "twitter",
            "content_type": "thread",
            "title": f"X Thread: {seg.theme}",
            "body": "\n\n".join(f"{i+1}/ {t}" for i, t in enumerate(pkg.twitter_thread)),
            "source": f"Video segment: {seg.theme}",
        })

    # Individual tweet posts from quotes
    for sq in social_quotes[:5]:
        tweet_text = f'"{sq["quote"]}" — {sq["speaker"]}, {config.COMPANY_NAME}\n\n@join_equi'
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."
        social_posts.append({
            "platform": "twitter",
            "content_type": "quote_tweet",
            "title": f"Quote: {sq['speaker']}",
            "body": tweet_text,
            "source": f"Video @ {sq['timestamp']}",
        })

    print(f"     Generated {len(social_posts)} social posts total")
    print(f"       LinkedIn: {sum(1 for p in social_posts if p['platform'] == 'linkedin')}")
    print(f"       Twitter: {sum(1 for p in social_posts if p['platform'] == 'twitter')}")

    # ── Step 6: Generate email teaser ───────────────────────────────────────
    print("\n  ⑥ Generating email teaser...")
    email_teaser = _generate_email_teaser(video, themed)
    print(f"     Email teaser: {len(email_teaser.split())} words")

    # ── Step 7: Build content calendar ──────────────────────────────────────
    print("\n  ⑦ Building 3-week content calendar...")

    calendar_items = []

    # Blog post
    calendar_items.append({
        "platform": "blog",
        "content_type": "article",
        "title": video.title,
        "body": blog[:200],
        "source": "Video transcript",
    })

    # Newsletter teaser
    calendar_items.append({
        "platform": "newsletter",
        "content_type": "feature",
        "title": f"New: {video.title}",
        "body": email_teaser[:200],
        "source": "Video transcript",
    })

    # Email
    calendar_items.append({
        "platform": "email",
        "content_type": "teaser",
        "title": f"New conversation: {video.title}",
        "body": email_teaser[:200],
        "source": "Video transcript",
    })

    # Add social posts
    calendar_items.extend(social_posts)

    calendar = build_calendar(calendar_items, weeks=3)
    print(f"     Calendar: {calendar.total_posts} entries over {calendar.weeks} weeks")
    print(f"     Period: {calendar.start_date} → {calendar.end_date}")

    # ── Step 8: Compliance review ───────────────────────────────────────────
    print("\n  ⑧ Running compliance review...")
    all_content = [
        ("blog", blog),
        ("email", email_teaser),
    ]
    for post in social_posts[:5]:
        all_content.append((post["platform"], post["body"]))

    compliance_results = []
    for platform, text in all_content:
        result = review_content(text, platform=platform)
        compliance_results.append((platform, result))
        if not result.passed or result.warnings:
            icon = "❌" if not result.passed else "⚠️"
            print(f"     {icon} {platform}: {result.review_notes[:60]}")

    passed = sum(1 for _, r in compliance_results if r.passed)
    print(f"     {passed}/{len(compliance_results)} pieces passed compliance")

    # ── Step 9: Save to database ────────────────────────────────────────────
    print("\n  ⑨ Saving to database...")
    batch_id = insert_batch(
        conn, workflow="video", founder="itay",
        source_summary=VIDEO_METADATA["title"],
        piece_count=len(social_posts) + 2,
    )

    # Blog post
    blog_pid = insert_piece(
        conn, workflow="video", source_type="video_transcript",
        source_text=VIDEO_TRANSCRIPT[:2000], founder="itay",
        platform="blog", content_type="article",
        title=video.title, body=blog, status="review",
    )

    # Email teaser
    email_pid = insert_piece(
        conn, workflow="video", source_type="video_transcript",
        source_text=VIDEO_TRANSCRIPT[:2000], founder="itay",
        platform="email", content_type="teaser",
        title=f"Email Teaser: {video.title}", body=email_teaser, status="review",
    )

    # Social posts
    social_pids = []
    for post in social_posts:
        pid = insert_piece(
            conn, workflow="video", source_type="video_transcript",
            source_text=VIDEO_TRANSCRIPT[:2000], founder="itay",
            platform=post["platform"], content_type=post["content_type"],
            title=post["title"], body=post["body"], status="review",
        )
        social_pids.append(pid)

    # Calendar entries
    for entry in calendar.entries:
        insert_calendar_entry(
            conn, batch_id=batch_id, piece_id=None,
            platform=entry.platform, scheduled_date=entry.date,
            scheduled_time=entry.time, content_preview=entry.content_preview,
        )

    print(f"     Batch #{batch_id}: {len(social_pids) + 2} pieces, {len(calendar.entries)} calendar entries")

    # ── Step 10: Write output files ─────────────────────────────────────────
    print("\n  ⑩ Writing output files...")

    # Blog post
    blog_path = config.OUTPUT_DIR / "workflow2_blog_post.md"
    blog_path.write_text(blog)
    print(f"  → {blog_path}")

    # Clip suggestions
    clips_data = [
        {
            "title": c.title,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "description": c.description,
            "key_quote": c.key_quote,
            "platform_fit": c.platform_fit,
        }
        for c in clips
    ]
    clips_path = config.OUTPUT_DIR / "workflow2_clips.json"
    clips_path.write_text(json.dumps(clips_data, indent=2))
    print(f"  → {clips_path}")

    # Social posts
    social_path = config.OUTPUT_DIR / "workflow2_social_posts.json"
    social_path.write_text(json.dumps(social_posts, indent=2))
    print(f"  → {social_path}")

    # Email teaser
    email_path = config.OUTPUT_DIR / "workflow2_email_teaser.md"
    email_path.write_text(email_teaser)
    print(f"  → {email_path}")

    # Content calendar
    cal_paths = save_calendar(calendar, str(config.OUTPUT_DIR))
    print(f"  → {cal_paths['csv']}")
    print(f"  → {cal_paths['json']}")

    # Full output JSON
    full_output = {
        "video": VIDEO_METADATA,
        "processing": {
            "segments": len(video.segments),
            "topics": video.topics_covered,
            "key_quotes": video.key_quotes[:10],
        },
        "clips": clips_data,
        "blog_word_count": blog_words,
        "social_posts_count": len(social_posts),
        "email_teaser_word_count": len(email_teaser.split()),
        "calendar": {
            "weeks": calendar.weeks,
            "total_entries": calendar.total_posts,
            "period": f"{calendar.start_date} → {calendar.end_date}",
        },
    }
    full_path = config.OUTPUT_DIR / "workflow2_output.json"
    full_path.write_text(json.dumps(full_output, indent=2))
    print(f"  → {full_path}")

    # Markdown summary
    md_path = config.OUTPUT_DIR / "workflow2_output.md"
    md_path.write_text(_format_markdown_output(video, themed, clips, blog, social_posts, email_teaser, calendar))
    print(f"  → {md_path}")

    conn.close()

    print(f"\n{'=' * 70}")
    print(f"  ✅ Workflow 2 complete")
    print(f"  • {len(clips)} clip suggestions")
    print(f"  • 1 blog post ({blog_words} words)")
    print(f"  • {len(social_posts)} social posts")
    print(f"  • 1 email teaser")
    print(f"  • {calendar.total_posts}-entry content calendar ({calendar.weeks} weeks)")
    print(f"  Output: {config.OUTPUT_DIR}/")
    print(f"{'=' * 70}\n")


def _generate_email_teaser(video, themed) -> str:
    """Generate an email teaser for the video content."""
    speakers = " and ".join(video.speakers)
    topics = ", ".join(video.topics_covered[:3])

    quotes = []
    for seg in themed[:2]:
        for q in seg.key_quotes[:1]:
            quotes.append(q)

    quote_block = ""
    if quotes:
        quote_block = f"\n\n> {quotes[0]}\n"

    return (
        f"We just published a new conversation between {speakers} on a topic we're hearing "
        f"about every day: {video.title.lower()}.\n\n"
        f"In {video.duration_minutes} minutes, they cover {topics} — and share the data "
        f"that's driving our conviction in alternatives for RIA portfolios."
        f"{quote_block}\n"
        f"Whether you're already allocating to alternatives or just starting to explore, "
        f"this conversation will give you a clear framework for thinking about the opportunity.\n\n"
        f"**[Watch the full conversation →]({config.WEBSITE})**\n\n"
        f"As always, we're happy to walk through how these ideas apply to your specific practice."
    )


def _format_markdown_output(video, themed, clips, blog, social_posts, email_teaser, calendar) -> str:
    """Format complete workflow 2 output as markdown."""
    lines = ["# Equi Content Engine — Workflow 2 Output\n"]
    lines.append(f"*Video: {video.title}*\n")
    lines.append(f"**Speakers:** {', '.join(video.speakers)} | "
                  f"**Duration:** {video.duration_minutes} min | "
                  f"**Words:** {video.total_words}\n")
    lines.append("---\n")

    # Topics
    lines.append("## Topics Covered\n")
    for topic in video.topics_covered:
        lines.append(f"- {topic}")
    lines.append("")

    # Clip suggestions
    lines.append("## Clip Suggestions\n")
    for i, clip in enumerate(clips, 1):
        lines.append(f"### Clip {i}: {clip.title}")
        lines.append(f"**Timestamps:** {clip.start_time} → {clip.end_time}")
        lines.append(f"**Best for:** {', '.join(clip.platform_fit)}")
        lines.append(f"**Key quote:** {clip.key_quote[:150]}")
        lines.append(f"**Description:** {clip.description}\n")

    # Blog post
    lines.append("## Blog Post\n")
    lines.append(blog + "\n")

    # Social posts
    lines.append("## Social Media Posts\n")
    for i, post in enumerate(social_posts, 1):
        lines.append(f"### Post {i} ({post['platform'].title()} — {post['content_type']})")
        lines.append(f"*Source: {post['source']}*\n")
        lines.append(post["body"][:500])
        if len(post["body"]) > 500:
            lines.append("...")
        lines.append("")

    # Email teaser
    lines.append("## Email Teaser\n")
    lines.append(email_teaser + "\n")

    # Calendar summary
    lines.append("## Content Calendar\n")
    lines.append(f"**Period:** {calendar.start_date} → {calendar.end_date} ({calendar.weeks} weeks)\n")
    lines.append(f"**Total entries:** {calendar.total_posts}\n")
    lines.append("| Date | Day | Time | Platform | Type | Title |")
    lines.append("|------|-----|------|----------|------|-------|")
    for entry in calendar.entries:
        lines.append(
            f"| {entry.date} | {entry.day_of_week} | {entry.time} | "
            f"{entry.platform.title()} | {entry.content_type} | {entry.title[:40]} |"
        )
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    run_workflow2_demo()
