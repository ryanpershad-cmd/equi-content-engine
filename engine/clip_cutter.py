"""
Video clip cutter — uses ffmpeg to extract clip segments from uploaded videos.
Stream-copies (no re-encoding) for speed.
"""
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "clips"


@dataclass
class CutResult:
    """Result of cutting a single clip."""
    clip_index: int
    title: str
    start_time: str
    end_time: str
    output_path: Path
    success: bool
    error: str = ""


def ensure_output_dir() -> Path:
    """Create clips output directory if needed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def cut_clip(
    input_path: str | Path,
    start_time: str,
    end_time: str,
    output_filename: str,
    output_dir: Path | None = None,
) -> Path:
    """
    Cut a single clip from a video file using ffmpeg stream copy.

    Args:
        input_path: Path to source video file
        start_time: Start timestamp (HH:MM:SS or MM:SS)
        end_time: End timestamp (HH:MM:SS or MM:SS)
        output_filename: Name for the output file (e.g., 'clip_1.mp4')
        output_dir: Output directory (defaults to output/clips/)

    Returns:
        Path to the generated clip file

    Raises:
        RuntimeError: If ffmpeg fails
    """
    out_dir = output_dir or ensure_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / output_filename

    cmd = [
        "ffmpeg", "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", str(input_path),
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        str(output_path),
    ]

    logger.info(f"Cutting clip: {start_time} → {end_time} → {output_filename}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        error_msg = result.stderr[-500:] if result.stderr else "Unknown ffmpeg error"
        raise RuntimeError(f"ffmpeg failed: {error_msg}")

    return output_path


def cut_all_clips(
    input_path: str | Path,
    clips: list[dict],
    job_id: str = "default",
) -> list[CutResult]:
    """
    Cut all suggested clips from a video.

    Args:
        input_path: Path to source video file
        clips: List of dicts with 'title', 'start_time', 'end_time'
        job_id: Unique identifier for this job (used in filenames)

    Returns:
        List of CutResult objects
    """
    out_dir = ensure_output_dir() / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, clip in enumerate(clips):
        filename = f"clip_{i + 1}.mp4"
        try:
            output_path = cut_clip(
                input_path=input_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                output_filename=filename,
                output_dir=out_dir,
            )
            results.append(CutResult(
                clip_index=i,
                title=clip.get("title", f"Clip {i + 1}"),
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                output_path=output_path,
                success=True,
            ))
        except Exception as e:
            logger.error(f"Failed to cut clip {i + 1}: {e}")
            results.append(CutResult(
                clip_index=i,
                title=clip.get("title", f"Clip {i + 1}"),
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                output_path=out_dir / filename,
                success=False,
                error=str(e),
            ))

    return results
