"""
Equi Content Engine — Web Application
FastAPI backend serving the content engine UI.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from db import (
    get_connection, init_db, insert_piece, insert_batch,
    update_piece_status, update_piece_body, get_all_pieces,
    get_piece, get_review_queue, get_calendar, get_dashboard_stats,
    insert_calendar_entry, insert_compliance_log,
)
from ingest.raw_input import parse_raw_input
from ingest.video_processor import process_transcript
from engine.tone_analyzer import analyze_tone
from engine.content_generator import generate_content_package
from engine.segment_extractor import extract_themed_segments, extract_social_quotes
from engine.blog_writer import generate_blog_post
from engine.calendar_builder import build_calendar
from review.compliance import review_content


app = FastAPI(title="Equi Content Engine", version="1.0.0")

# Static files & templates
WEB_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")

# Initialize DB on startup
@app.on_event("startup")
def startup():
    conn = get_connection()
    init_db(conn)
    conn.close()


# ── Pages ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# ── API: Dashboard ───────────────────────────────────────────────────────────

@app.get("/api/dashboard")
async def api_dashboard():
    conn = get_connection()
    stats = get_dashboard_stats(conn)
    conn.close()
    return stats


# ── API: Workflow 1 — Quick Content ──────────────────────────────────────────

@app.post("/api/generate")
async def api_generate(request: Request):
    """Generate multi-platform content from raw founder input."""
    data = await request.json()
    raw_text = data.get("text", "").strip()
    founder = data.get("founder", "tory").lower()

    if not raw_text:
        return JSONResponse({"error": "No input text provided"}, status_code=400)

    # Process
    parsed = parse_raw_input(raw_text, founder=founder)
    analysis = analyze_tone(raw_text, founder=founder)
    package = generate_content_package(parsed, analysis)

    # Compliance review
    compliance = {}
    all_passed = True
    for platform, text in [
        ("linkedin", package.linkedin),
        ("newsletter", package.newsletter),
        ("twitter", "\n".join(package.twitter_thread)),
        ("email", package.email_snippet),
    ]:
        result = review_content(text, platform=platform)
        compliance[platform] = {
            "passed": result.passed,
            "flags": len(result.flags),
            "warnings": len(result.warnings),
            "notes": result.review_notes,
            "flag_details": [{"type": f["type"], "phrase": f["phrase"]} for f in result.flags],
            "warning_details": [{"type": w["type"], "phrase": w["phrase"]} for w in result.warnings],
        }
        if not result.passed:
            all_passed = False

    # Save to database
    conn = get_connection()
    status = "review" if all_passed else "draft"

    batch_id = insert_batch(
        conn, workflow="quick", founder=founder,
        source_summary=raw_text[:200], piece_count=4,
    )

    pieces = {}
    piece_data = [
        ("linkedin", "post", f"LinkedIn: {analysis.primary_topic}", package.linkedin),
        ("newsletter", "blurb", f"Newsletter: {analysis.primary_topic}", package.newsletter),
        ("twitter", "thread", f"X Thread: {analysis.primary_topic}",
         "\n\n".join(f"{i+1}/ {t}" for i, t in enumerate(package.twitter_thread))),
        ("email", "snippet", f"Email: {analysis.primary_topic}", package.email_snippet),
    ]

    for platform, ctype, title, body in piece_data:
        pid = insert_piece(
            conn, workflow="quick", source_type=parsed.input_type,
            source_text=raw_text, founder=founder,
            platform=platform, content_type=ctype,
            title=title, body=body, status=status,
        )
        cr = compliance.get(platform, {})
        flags = (cr.get("flag_details", []) + cr.get("warning_details", []))
        flag_phrases = [f.get("phrase", "") for f in flags]
        insert_compliance_log(
            conn, pid, action="auto_review",
            notes=cr.get("notes", ""), flags=flag_phrases if flag_phrases else None,
        )
        pieces[platform] = {"id": pid, "body": body, "status": status, "title": title}

    conn.close()

    return {
        "success": True,
        "batch_id": batch_id,
        "method": package.generation_method,
        "analysis": {
            "input_type": parsed.input_type,
            "topic": analysis.primary_topic,
            "sentiment": analysis.sentiment,
            "angle": analysis.recommended_angle,
            "urgency": analysis.urgency,
        },
        "content": {
            "linkedin": package.linkedin,
            "newsletter": package.newsletter,
            "twitter_thread": package.twitter_thread,
            "email": package.email_snippet,
        },
        "pieces": pieces,
        "compliance": compliance,
    }


# ── API: Workflow 2 — Video Content ──────────────────────────────────────────

@app.post("/api/process-video")
async def api_process_video(request: Request):
    """Process a video transcript into a content library."""
    data = await request.json()
    transcript = data.get("transcript", "").strip()
    title = data.get("title", "Video Conversation")
    speakers_str = data.get("speakers", "Itay, Tory")
    duration = data.get("duration", 30)

    if not transcript:
        return JSONResponse({"error": "No transcript provided"}, status_code=400)

    speakers = [s.strip() for s in speakers_str.split(",")]

    # Process transcript
    video = process_transcript(transcript, title=title, speakers=speakers,
                               duration_minutes=duration)

    # Extract segments & quotes
    themed = extract_themed_segments(video)
    social_quotes = extract_social_quotes(video, max_quotes=10)

    # Generate blog post
    blog = generate_blog_post(video, themed)

    # Generate social posts from themed segments
    social_posts = []
    for seg in themed[:3]:
        seg_text = " ".join(s.text for s in seg.segments)
        analysis = analyze_tone(seg_text, founder="itay")
        parsed = parse_raw_input(seg_text, founder="itay")
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

    # Quote tweets
    for sq in social_quotes[:5]:
        tweet = f'"{sq["quote"]}" — {sq["speaker"]}, {config.COMPANY_NAME}\n\n@join_equi'
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        social_posts.append({
            "platform": "twitter",
            "content_type": "quote_tweet",
            "title": f"Quote: {sq['speaker']}",
            "body": tweet,
            "source": f"Video @ {sq['timestamp']}",
        })

    # Email teaser
    speakers_joined = " and ".join(video.speakers)
    topics_str = ", ".join(video.topics_covered[:3])
    email_teaser = (
        f"We just published a new conversation between {speakers_joined} on "
        f"{video.title.lower()}.\n\n"
        f"In {video.duration_minutes} minutes, they cover {topics_str} — and share the data "
        f"driving our conviction in alternatives for RIA portfolios.\n\n"
        f"Whether you're already allocating to alternatives or just starting to explore, "
        f"this conversation will give you a clear framework.\n\n"
        f"**[Watch the full conversation →]({config.WEBSITE})**"
    )

    # Build calendar
    cal_items = [{"platform": "blog", "content_type": "article", "title": title,
                  "body": blog[:200], "source": "Video"}]
    cal_items.append({"platform": "newsletter", "content_type": "feature",
                      "title": f"New: {title}", "body": email_teaser[:200], "source": "Video"})
    cal_items.append({"platform": "email", "content_type": "teaser",
                      "title": title, "body": email_teaser[:200], "source": "Video"})
    cal_items.extend(social_posts)

    calendar = build_calendar(cal_items, weeks=3)

    # Clips
    clips = [
        {
            "title": c.title,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "description": c.description,
            "key_quote": c.key_quote,
            "platform_fit": c.platform_fit,
        }
        for c in video.clip_suggestions
    ]

    # Save to database
    conn = get_connection()
    batch_id = insert_batch(
        conn, workflow="video", founder="itay",
        source_summary=title, piece_count=len(social_posts) + 2,
    )

    insert_piece(
        conn, workflow="video", source_type="video_transcript",
        source_text=transcript[:2000], founder="itay",
        platform="blog", content_type="article",
        title=title, body=blog, status="review",
    )
    insert_piece(
        conn, workflow="video", source_type="video_transcript",
        source_text=transcript[:2000], founder="itay",
        platform="email", content_type="teaser",
        title=f"Email: {title}", body=email_teaser, status="review",
    )
    for post in social_posts:
        insert_piece(
            conn, workflow="video", source_type="video_transcript",
            source_text=transcript[:2000], founder="itay",
            platform=post["platform"], content_type=post["content_type"],
            title=post["title"], body=post["body"], status="review",
        )

    for entry in calendar.entries:
        insert_calendar_entry(
            conn, batch_id=batch_id, piece_id=None,
            platform=entry.platform, scheduled_date=entry.date,
            scheduled_time=entry.time, content_preview=entry.content_preview,
        )

    conn.close()

    return {
        "success": True,
        "batch_id": batch_id,
        "video": {
            "title": video.title,
            "speakers": video.speakers,
            "duration": video.duration_minutes,
            "segments": len(video.segments),
            "topics": video.topics_covered,
            "word_count": video.total_words,
        },
        "clips": clips,
        "blog": blog,
        "social_posts": social_posts,
        "email_teaser": email_teaser,
        "calendar": {
            "weeks": calendar.weeks,
            "total_entries": calendar.total_posts,
            "start_date": calendar.start_date,
            "end_date": calendar.end_date,
            "entries": [
                {
                    "date": e.date,
                    "day": e.day_of_week,
                    "time": e.time,
                    "platform": e.platform,
                    "content_type": e.content_type,
                    "title": e.title,
                    "content_preview": e.content_preview,
                    "status": e.status,
                }
                for e in calendar.entries
            ],
        },
        "quotes": social_quotes[:8],
    }


# ── API: Content Management ─────────────────────────────────────────────────

@app.get("/api/content")
async def api_list_content(status: str = None, platform: str = None,
                           limit: int = 100):
    """List content pieces with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM content_pieces WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/content/{piece_id}")
async def api_get_content(piece_id: int):
    conn = get_connection()
    piece = get_piece(conn, piece_id)
    conn.close()
    if not piece:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return piece


@app.put("/api/content/{piece_id}/status")
async def api_update_status(piece_id: int, request: Request):
    data = await request.json()
    new_status = data.get("status", "")
    notes = data.get("notes")

    if new_status not in config.VALID_STATUSES:
        return JSONResponse({"error": f"Invalid status: {new_status}"}, status_code=400)

    conn = get_connection()
    update_piece_status(conn, piece_id, new_status, notes)
    insert_compliance_log(conn, piece_id, action=f"status_change_to_{new_status}",
                          reviewer="web_ui", notes=notes)
    piece = get_piece(conn, piece_id)
    conn.close()
    return piece


@app.put("/api/content/{piece_id}/body")
async def api_update_body(piece_id: int, request: Request):
    data = await request.json()
    body = data.get("body", "")
    conn = get_connection()
    update_piece_body(conn, piece_id, body)
    piece = get_piece(conn, piece_id)
    conn.close()
    return piece


# ── API: Review Queue ────────────────────────────────────────────────────────

@app.get("/api/review")
async def api_review_queue():
    conn = get_connection()
    pieces = get_review_queue(conn)
    conn.close()
    return pieces


# ── API: Calendar ────────────────────────────────────────────────────────────

@app.get("/api/calendar")
async def api_calendar(start: str = None, end: str = None):
    conn = get_connection()
    entries = get_calendar(conn, start, end)
    conn.close()
    return entries


# ── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
