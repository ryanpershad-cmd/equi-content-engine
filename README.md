# Equi CEO Content Repurposing & Distribution Engine

A content engine that transforms raw founder input — voice memos, bullet points, Slack messages, and video transcripts — into polished, multi-platform content for Equi's marketing and thought leadership.

---

## What it does

```
Raw Founder Input                    Long-Form Video
(voice memo, bullets, Slack)         (30-45 min transcript)
         ↓                                    ↓
   Parse & analyze                     Parse & segment
         ↓                                    ↓
   Detect tone, topic,                Extract key moments,
   market context                     quotes, themes
         ↓                                    ↓
   Generate content                   Generate content library
   for 4 platforms                    (blog, social, email)
         ↓                                    ↓
   Compliance review                  Build 3-week calendar
         ↓                                    ↓
   draft → review → approved → scheduled → published
```

---

## Two workflows

### Workflow 1: Quick Content

Turn raw founder thinking into distribution-ready content:

| Input | → | Output |
|-------|---|--------|
| Voice memo transcript | | LinkedIn post (500-800 words) |
| Bullet points | | Newsletter blurb (200-300 words) |
| Slack message | | X/Twitter thread (4-7 tweets) |
| Rough paragraph | | Email snippet (150-200 words) |

Each piece is automatically reviewed for SEC compliance, assigned a status, and tracked in the database.

### Workflow 2: Video → Content Library

Accept a video file or transcript and produce a full content library:

- **Video upload** — MP4, MOV, WebM, MP3, WAV, M4A (up to 500MB)
- **Automatic transcription** — Whisper (OpenAI, local) with timestamps
- **5 clip suggestions** with timestamps, titles, and key quotes
- **Actual video clips** — ffmpeg cuts the source video into downloadable MP4 segments
- **Blog post** (800-1200 words)
- **8-10 social media posts** (LinkedIn + X/Twitter)
- **Email teaser** (200 words)
- **3-week content calendar** (CSV + JSON) scheduling assets across platforms

Two input modes: upload a raw video file (transcription + clip cutting handled automatically) or paste an existing transcript.

---

## Content pipeline

Every piece of content flows through a tracked state machine:

```
draft → review → approved → scheduled → published
                    ↓
                rejected (with notes)
```

The compliance module automatically flags:
- Prohibited language (guarantees, "risk-free", specific return claims)
- Warning phrases (past performance references without disclaimers)
- Missing disclaimers on long-form content
- Competitor disparagement

---

## Web UI

A modern single-page web interface for operating the content engine:

| Page | What it does |
|------|-------------|
| **Dashboard** | Pipeline stats, recent activity feed |
| **Quick Content** | Paste raw input → generate multi-platform content, review compliance, approve/schedule |
| **Video Content** | Upload video files or paste transcripts → auto-transcribe with Whisper → view clips with download links, blog, social posts, calendar |
| **Calendar** | Filter scheduled content by platform and date |
| **Review Queue** | Approve, reject, or edit pending content |

---

## Architecture

```
equi-content-engine/
├── config.py                    # All tunable parameters (company, platforms, compliance)
├── requirements.txt
├── .env.example
│
├── ingest/
│   ├── raw_input.py            # Parse raw founder input (voice/bullets/slack)
│   └── video_processor.py      # Transcript parsing, segment extraction
│
├── engine/
│   ├── tone_analyzer.py        # Topic detection, sentiment, market context
│   ├── content_generator.py    # Claude API + template fallbacks
│   ├── segment_extractor.py    # Theme extraction from video segments
│   ├── blog_writer.py          # Long-form blog post generation
│   ├── calendar_builder.py     # Multi-week content calendar
│   └── clip_cutter.py          # ffmpeg video clip cutting
│
├── review/
│   └── compliance.py           # SEC compliance flagging + approval workflow
│
├── db/
│   └── __init__.py             # SQLite schema + CRUD helpers
│
├── web/
│   ├── app.py                  # FastAPI backend (API + page serving)
│   ├── static/
│   │   ├── style.css           # Custom stylesheet (navy + white + accent blue)
│   │   └── app.js              # SPA frontend logic
│   └── templates/
│       └── index.html          # Single-page app template
│
├── sample_data/
│   ├── founder_inputs.py       # 3 sample inputs (voice memo, bullets, Slack)
│   └── video_transcript.py     # 30-min Itay + Tory conversation transcript
│
├── output/                     # Generated content files (md, json, csv)
│
├── demo_workflow1.py           # CLI demo: raw input → multi-platform content
├── demo_workflow2.py           # CLI demo: video → content library + calendar
└── run_production.py           # Main entry point
```

---

## Setup

### Requirements

```bash
pip install -r requirements.txt
```

Dependencies: `anthropic`, `python-dotenv`, `fastapi`, `uvicorn`, `jinja2`, `python-multipart`

For video upload & clip cutting (Workflow 2 full pipeline):
```bash
pip install openai-whisper
apt install ffmpeg    # or brew install ffmpeg on macOS
```

### Environment variables (`.env`)

```
ANTHROPIC_API_KEY=sk-ant-...    # Optional — system works without it
```

### Run the demos (no API key required)

```bash
# Both workflows
python run_production.py

# Individual workflows
python demo_workflow1.py        # Quick content (3 sample inputs)
python demo_workflow2.py        # Video content (30-min transcript)
```

### Run the web UI

```bash
python -m web.app
# or
uvicorn web.app:app --host 0.0.0.0 --port 8000 --reload
```

Then open [http://localhost:8000](http://localhost:8000).

---

## AI generation

The engine uses Claude (Anthropic API) for content generation when an API key is available. Every Claude call has a **template fallback** that produces quality output without any API:

| Component | Claude | Template |
|-----------|--------|----------|
| LinkedIn post | Custom prompt with brand voice, founder personality | Structured generation from key points, stats, topics |
| Newsletter blurb | Punchy format with CTA | Modular template with stats, insight, product reference |
| X/Twitter thread | Platform-optimized, 280-char enforced | Key points → numbered tweets with hooks |
| Email snippet | Warm professional tone | Opening + insight + CTA framework |
| Blog post | Full article from themed segments + quotes | Section-based assembly from themes and narratives |

---

## Compliance rules

| Severity | Check | Examples |
|----------|-------|----------|
| 🚫 **Hard flag** (blocked) | Prohibited language | "guaranteed", "risk-free", "will outperform" |
| 🚫 **Hard flag** (blocked) | Specific return claims | "generated 12% return", "8% yield" |
| ⚠️ **Warning** (review) | Performance references | "past performance", "outperformed", "alpha generation" |
| ⚠️ **Warning** (review) | Missing disclaimers | Long-form content without "for informational purposes" |
| ⚠️ **Warning** (review) | Competitor disparagement | "unlike other failing funds" |

---

## Content calendar

Workflow 2 generates a multi-week content calendar with platform-optimized scheduling:

| Platform | Posts/week | Best times (ET) | Days |
|----------|-----------|-----------------|------|
| LinkedIn | 2 | 8am, 10am, 12pm | Tue, Wed |
| X/Twitter | 3 | 7am, 12pm, 5pm | Tue-Thu |
| Newsletter | Biweekly | 9am | Wed |
| Email | 1 | 10am, 2pm | Tue |
| Blog | Biweekly | 10am | Wed |

Output formats: CSV (for spreadsheet import) and JSON (for programmatic use).

---

## Database schema

SQLite tracks all content through its lifecycle:

- **content_pieces** — Every generated piece with status, platform, body, compliance notes
- **content_batches** — Groups of pieces from a single generation run
- **calendar_entries** — Scheduled distribution slots
- **compliance_log** — Audit trail of every review action

---

## Sample outputs

All sample outputs are included in the `output/` directory:

| File | Description |
|------|-------------|
| `workflow1_output.md` | Full markdown with all 3 input → 4-platform content packages |
| `workflow1_output.json` | Structured JSON with content, analysis, and compliance results |
| `workflow2_blog_post.md` | Blog post generated from 30-min video transcript |
| `workflow2_clips.json` | 5 clip suggestions with timestamps and key quotes |
| `workflow2_social_posts.json` | 11 social media posts (LinkedIn + X) |
| `workflow2_email_teaser.md` | Email teaser for the video content |
| `content_calendar.csv` | 3-week, 22-entry content calendar |
| `content_calendar.json` | Calendar in JSON format |
| `compliance_*.txt` | Individual compliance reports per content piece |

---

## Key parameters (`config.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CLAUDE_MODEL` | claude-sonnet-4-20250514 | Model for content generation |
| `CALENDAR_WEEKS` | 3 | Default calendar span |
| `POSTS_PER_WEEK_LINKEDIN` | 2 | LinkedIn posting cadence |
| `POSTS_PER_WEEK_TWITTER` | 3 | X posting cadence |
| `COMPLIANCE_AUTO_FLAGS` | 12 phrases | Prohibited language list |
| `COMPLIANCE_WARNING_PHRASES` | 6 phrases | Review-recommended phrases |
