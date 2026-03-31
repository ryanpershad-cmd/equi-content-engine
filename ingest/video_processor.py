"""
Video/transcript processor for Workflow 2.
Parses long-form transcripts, identifies speakers, segments, and key moments.
Supports Whisper-based transcription from video/audio files.
"""
import re
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """A contiguous segment of the transcript."""
    speaker: str
    text: str
    start_time: str      # HH:MM:SS
    end_time: str        # HH:MM:SS
    topic: str = ""
    is_key_moment: bool = False
    quote_worthy: bool = False


@dataclass
class ClipSuggestion:
    """A suggested short clip from the video."""
    title: str
    start_time: str
    end_time: str
    description: str
    key_quote: str
    platform_fit: list[str] = field(default_factory=list)  # which platforms this clip suits


@dataclass
class ProcessedVideo:
    """Full processed output from a video transcript."""
    title: str
    speakers: list[str]
    duration_minutes: int
    total_words: int
    segments: list[TranscriptSegment] = field(default_factory=list)
    clip_suggestions: list[ClipSuggestion] = field(default_factory=list)
    key_quotes: list[str] = field(default_factory=list)
    topics_covered: list[str] = field(default_factory=list)
    raw_transcript: str = ""


def parse_timestamp(ts: str) -> int:
    """Convert HH:MM:SS or MM:SS to total seconds."""
    parts = ts.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0


def seconds_to_timestamp(secs: int) -> str:
    """Convert total seconds to HH:MM:SS."""
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_timestamped_transcript(text: str) -> list[TranscriptSegment]:
    """
    Parse a transcript with timestamps and speaker labels.

    Expected formats:
        [00:00:00] Speaker: text
        (00:00) Speaker: text
        00:00:00 - Speaker: text
    """
    # Pattern: optional brackets/parens, timestamp, optional separator, speaker, colon, text
    pattern = r'[\[\(]?(\d{1,2}:\d{2}(?::\d{2})?)[\]\)]?\s*[-–]?\s*([A-Za-z]+)\s*:\s*(.+?)(?=[\[\(]?\d{1,2}:\d{2}|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)

    segments = []
    for i, (timestamp, speaker, content) in enumerate(matches):
        # Determine end time from next segment or estimate
        if i + 1 < len(matches):
            end_ts = matches[i + 1][0]
        else:
            start_secs = parse_timestamp(timestamp)
            end_ts = seconds_to_timestamp(start_secs + 120)  # estimate 2 min

        # Normalize timestamp to HH:MM:SS
        if timestamp.count(":") == 1:
            timestamp = "00:" + timestamp

        if end_ts.count(":") == 1:
            end_ts = "00:" + end_ts

        segments.append(TranscriptSegment(
            speaker=speaker.strip(),
            text=content.strip(),
            start_time=timestamp,
            end_time=end_ts,
        ))

    return segments


def identify_key_moments(segments: list[TranscriptSegment]) -> list[TranscriptSegment]:
    """Mark segments that contain key insights, data points, or quotable moments."""
    key_indicators = [
        "the key thing", "here's what matters", "the data shows",
        "what we're seeing", "the opportunity", "game-changer",
        "most important", "the real question", "here's why",
        "what advisors need to know", "bottom line", "the difference",
        "the challenge", "what makes us different", "critical",
    ]
    stat_pattern = re.compile(r'\d+\.?\d*\s*%|\$[\d,.]+\s*(?:billion|B|million|M)')

    for seg in segments:
        lower = seg.text.lower()
        has_key_phrase = any(k in lower for k in key_indicators)
        has_stat = bool(stat_pattern.search(seg.text))
        word_count = len(seg.text.split())

        if has_key_phrase or has_stat:
            seg.is_key_moment = True
        if has_stat and word_count < 100:
            seg.quote_worthy = True
        elif has_key_phrase and word_count < 80:
            seg.quote_worthy = True

    return segments


def extract_key_quotes(segments: list[TranscriptSegment], max_quotes: int = 10) -> list[str]:
    """Extract the most quotable lines from the transcript."""
    quotes = []
    for seg in segments:
        if not seg.quote_worthy and not seg.is_key_moment:
            continue
        # Split into sentences and find the punchiest ones
        sentences = re.split(r'(?<=[.!?])\s+', seg.text)
        for sent in sentences:
            words = sent.split()
            if 10 <= len(words) <= 40:
                quotes.append(f'"{sent.strip()}" — {seg.speaker}')
                if len(quotes) >= max_quotes:
                    return quotes
    return quotes


def suggest_clips(segments: list[TranscriptSegment], max_clips: int = 5) -> list[ClipSuggestion]:
    """Identify the best segments for short-form clips."""
    candidates = [s for s in segments if s.is_key_moment]

    # If not enough key moments, include longer substantive segments
    if len(candidates) < max_clips:
        remaining = [s for s in segments if not s.is_key_moment and len(s.text.split()) > 50]
        candidates.extend(remaining[:max_clips - len(candidates)])

    clips = []
    for seg in candidates[:max_clips]:
        # Extract a key quote from this segment
        sentences = re.split(r'(?<=[.!?])\s+', seg.text)
        key_quote = max(sentences, key=lambda s: len(s.split())) if sentences else seg.text[:100]

        # Determine platform fit
        word_count = len(seg.text.split())
        platforms = ["linkedin"]
        if word_count < 60:
            platforms.append("twitter")
        if word_count > 30:
            platforms.extend(["blog", "newsletter"])

        clips.append(ClipSuggestion(
            title=_generate_clip_title(seg),
            start_time=seg.start_time,
            end_time=seg.end_time,
            description=seg.text[:200] + ("..." if len(seg.text) > 200 else ""),
            key_quote=key_quote.strip(),
            platform_fit=platforms,
        ))

    return clips


def _generate_clip_title(segment: TranscriptSegment) -> str:
    """Generate a descriptive title for a clip based on content."""
    text = segment.text.lower()
    if "correlation" in text or "60/40" in text:
        return "The Correlation Problem in Traditional Portfolios"
    if "tender offer" in text:
        return "How the Tender Offer Fund Changes the Game"
    if "ria" in text and ("access" in text or "infrastructure" in text):
        return "Why RIAs Are Underallocated to Alternatives"
    if "diligence" in text or "due diligence" in text:
        return "The Due Diligence Advantage"
    if "multi-strategy" in text or "diversif" in text:
        return "Building a Diversified Hedge Fund Portfolio"
    if "risk" in text or "drawdown" in text:
        return "Managing Risk in Alternative Allocations"
    if "alpha" in text or "return" in text:
        return "Generating Uncorrelated Alpha"
    # Fallback: use first substantive sentence
    sentences = re.split(r'(?<=[.!?])\s+', segment.text)
    if sentences:
        title = sentences[0][:60]
        if len(sentences[0]) > 60:
            title = title.rsplit(" ", 1)[0] + "..."
        return title
    return f"Segment at {segment.start_time}"


def detect_topics(segments: list[TranscriptSegment]) -> list[str]:
    """Identify the main topics discussed across segments."""
    topic_keywords = {
        "Market Environment & Correlations": ["correlation", "60/40", "market environment", "volatility", "macro"],
        "RIA Alternatives Access": ["ria", "advisor", "access", "infrastructure", "independent"],
        "Hedge Fund Allocations": ["hedge fund", "multi-strategy", "allocation", "alternative"],
        "Tender Offer Fund": ["tender offer", "registered fund", "ria allocation"],
        "Due Diligence & Manager Selection": ["diligence", "manager selection", "underwriting", "track record"],
        "Portfolio Construction": ["portfolio construction", "diversification", "uncorrelated", "risk-adjusted"],
        "Industry Trends": ["industry", "inflow", "trend", "institutional", "blackrock"],
        "Operational Infrastructure": ["operational", "infrastructure", "lp agreement", "capital call"],
    }

    found = []
    all_text = " ".join(s.text.lower() for s in segments)
    for topic, keywords in topic_keywords.items():
        if any(kw in all_text for kw in keywords):
            found.append(topic)
    return found


def transcribe_file(file_path: str | Path, model_name: str = "base") -> str:
    """
    Transcribe a video or audio file using OpenAI Whisper (local model).

    Args:
        file_path: Path to video/audio file (mp4, mov, webm, mp3, wav, m4a)
        model_name: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')

    Returns:
        Timestamped transcript string in the format:
            [HH:MM:SS] Speaker: text

    Note: Whisper doesn't do speaker diarization, so all segments are attributed
    to 'Speaker'. For multi-speaker identification, a separate diarization step
    would be needed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Extract audio to wav if it's a video file (Whisper works best with audio)
    audio_path = file_path
    video_exts = {".mp4", ".mov", ".webm"}
    if file_path.suffix.lower() in video_exts:
        audio_path = file_path.with_suffix(".wav")
        logger.info(f"Extracting audio from video: {file_path} → {audio_path}")
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-vn",                    # no video
                "-acodec", "pcm_s16le",   # PCM 16-bit
                "-ar", "16000",           # 16kHz (Whisper's expected rate)
                "-ac", "1",               # mono
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr[-300:]}")

    try:
        import whisper
    except ImportError:
        raise ImportError(
            "openai-whisper is not installed. Install with: pip install openai-whisper"
        )

    logger.info(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    logger.info(f"Transcribing: {audio_path}")
    result = model.transcribe(
        str(audio_path),
        verbose=False,
        word_timestamps=False,
    )

    # Build timestamped transcript
    lines = []
    for segment in result.get("segments", []):
        start_secs = int(segment["start"])
        timestamp = seconds_to_timestamp(start_secs)
        text = segment["text"].strip()
        if text:
            lines.append(f"[{timestamp}] Speaker: {text}")

    transcript = "\n\n".join(lines)

    # Clean up extracted audio if we created it
    if audio_path != file_path and audio_path.exists():
        try:
            audio_path.unlink()
        except OSError:
            pass

    logger.info(f"Transcription complete: {len(lines)} segments")
    return transcript


def process_video_file(
    file_path: str | Path,
    title: str = "",
    speakers: list[str] | None = None,
    duration_minutes: int = 30,
    whisper_model: str = "base",
) -> tuple[ProcessedVideo, str]:
    """
    Full pipeline: transcribe a video/audio file, then process the transcript.

    Args:
        file_path: Path to video/audio file
        title: Video title
        speakers: Speaker names
        duration_minutes: Estimated duration
        whisper_model: Whisper model size to use

    Returns:
        Tuple of (ProcessedVideo, raw_transcript_text)
    """
    transcript = transcribe_file(file_path, model_name=whisper_model)
    video = process_transcript(
        transcript,
        title=title,
        speakers=speakers,
        duration_minutes=duration_minutes,
    )
    return video, transcript


def process_transcript(text: str, title: str = "", speakers: list[str] | None = None,
                       duration_minutes: int = 30) -> ProcessedVideo:
    """
    Full transcript processing pipeline.

    Args:
        text: Raw transcript text (timestamped preferred)
        title: Video title
        speakers: List of speaker names
        duration_minutes: Estimated duration

    Returns:
        ProcessedVideo with segments, clips, quotes, and topics
    """
    segments = parse_timestamped_transcript(text)

    # Fallback: if no timestamps detected, create single-segment representation
    if not segments:
        segments = [TranscriptSegment(
            speaker=speakers[0] if speakers else "Speaker",
            text=text,
            start_time="00:00:00",
            end_time=seconds_to_timestamp(duration_minutes * 60),
        )]

    segments = identify_key_moments(segments)
    clips = suggest_clips(segments)
    quotes = extract_key_quotes(segments)
    topics = detect_topics(segments)

    if not speakers:
        speakers = list({s.speaker for s in segments})

    return ProcessedVideo(
        title=title,
        speakers=speakers,
        duration_minutes=duration_minutes,
        total_words=sum(len(s.text.split()) for s in segments),
        segments=segments,
        clip_suggestions=clips,
        key_quotes=quotes,
        topics_covered=topics,
        raw_transcript=text,
    )
