"""
Calendar builder — generates multi-week content distribution calendars.
Schedules content across platforms with appropriate cadence and timing.
"""
import csv
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from io import StringIO

import config


@dataclass
class CalendarEntry:
    """A single scheduled content item."""
    date: str               # YYYY-MM-DD
    day_of_week: str
    time: str               # HH:MM
    platform: str
    content_type: str
    title: str
    content_preview: str    # First 200 chars
    full_content: str
    status: str = "scheduled"
    source: str = ""        # Which input/video this came from
    notes: str = ""


@dataclass
class ContentCalendar:
    """Complete multi-week content calendar."""
    start_date: str
    end_date: str
    entries: list[CalendarEntry] = field(default_factory=list)
    weeks: int = 3
    total_posts: int = 0


# Platform optimal posting times (ET)
POSTING_TIMES = {
    "linkedin": ["08:00", "10:00", "12:00"],
    "twitter": ["07:00", "12:00", "17:00"],
    "newsletter": ["09:00"],
    "email": ["10:00", "14:00"],
    "blog": ["10:00"],
}

# Platform weekly cadence
WEEKLY_CADENCE = {
    "linkedin": 2,
    "twitter": 3,
    "newsletter": 0.5,   # every other week
    "email": 1,
    "blog": 0.5,          # every other week
}


def build_calendar(content_items: list[dict], start_date: str | None = None,
                   weeks: int = 3) -> ContentCalendar:
    """
    Build a content distribution calendar from a list of content items.

    Args:
        content_items: List of dicts with keys: platform, content_type, title, body, source
        start_date: Start date (YYYY-MM-DD), defaults to next Monday
        weeks: Number of weeks to schedule

    Returns:
        ContentCalendar with scheduled entries
    """
    if not start_date:
        today = datetime.now()
        # Next Monday
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        start = today + timedelta(days=days_until_monday)
        start_date = start.strftime("%Y-%m-%d")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(weeks=weeks)

    calendar = ContentCalendar(
        start_date=start_date,
        end_date=end.strftime("%Y-%m-%d"),
        weeks=weeks,
    )

    # Group content by platform
    by_platform: dict[str, list[dict]] = {}
    for item in content_items:
        plat = item.get("platform", "linkedin")
        by_platform.setdefault(plat, []).append(item)

    # Schedule each platform according to cadence
    for platform, items in by_platform.items():
        cadence = WEEKLY_CADENCE.get(platform, 1)
        times = POSTING_TIMES.get(platform, ["10:00"])
        item_idx = 0

        for week in range(weeks):
            week_start = start + timedelta(weeks=week)

            # How many posts this week
            if cadence < 1:
                # Post every N weeks
                if week % int(1 / cadence) != 0:
                    continue
                posts_this_week = 1
            else:
                posts_this_week = int(cadence)

            # Distribute posts across weekdays (Tue, Wed, Thu preferred)
            preferred_days = [1, 2, 3, 0, 4]  # Tue, Wed, Thu, Mon, Fri
            post_days = preferred_days[:posts_this_week]

            for day_offset in post_days:
                if item_idx >= len(items):
                    item_idx = 0  # Cycle if we run out

                post_date = week_start + timedelta(days=day_offset)
                if post_date >= end:
                    break

                item = items[item_idx]
                time_slot = times[item_idx % len(times)]

                calendar.entries.append(CalendarEntry(
                    date=post_date.strftime("%Y-%m-%d"),
                    day_of_week=post_date.strftime("%A"),
                    time=time_slot,
                    platform=platform,
                    content_type=item.get("content_type", "post"),
                    title=item.get("title", f"{platform.title()} Post"),
                    content_preview=item.get("body", "")[:200],
                    full_content=item.get("body", ""),
                    source=item.get("source", ""),
                    status="scheduled",
                ))

                item_idx += 1

    # Sort by date and time
    calendar.entries.sort(key=lambda e: (e.date, e.time))
    calendar.total_posts = len(calendar.entries)

    return calendar


def calendar_to_csv(calendar: ContentCalendar) -> str:
    """Export calendar to CSV string."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date", "Day", "Time (ET)", "Platform", "Content Type",
        "Title", "Content Preview", "Status", "Source", "Notes"
    ])

    for entry in calendar.entries:
        writer.writerow([
            entry.date, entry.day_of_week, entry.time,
            entry.platform.title(), entry.content_type,
            entry.title, entry.content_preview[:150],
            entry.status, entry.source, entry.notes,
        ])

    return output.getvalue()


def calendar_to_json(calendar: ContentCalendar) -> str:
    """Export calendar to JSON string."""
    data = {
        "start_date": calendar.start_date,
        "end_date": calendar.end_date,
        "weeks": calendar.weeks,
        "total_posts": calendar.total_posts,
        "entries": [
            {
                "date": e.date,
                "day": e.day_of_week,
                "time": e.time,
                "platform": e.platform,
                "content_type": e.content_type,
                "title": e.title,
                "content_preview": e.content_preview,
                "full_content": e.full_content,
                "status": e.status,
                "source": e.source,
            }
            for e in calendar.entries
        ],
    }
    return json.dumps(data, indent=2)


def save_calendar(calendar: ContentCalendar, output_dir: str) -> dict[str, str]:
    """Save calendar in both CSV and JSON formats. Returns paths."""
    from pathlib import Path
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / "content_calendar.csv"
    json_path = out / "content_calendar.json"

    csv_path.write_text(calendar_to_csv(calendar))
    json_path.write_text(calendar_to_json(calendar))

    return {"csv": str(csv_path), "json": str(json_path)}
