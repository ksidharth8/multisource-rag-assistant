import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


def extract_youtube_video_id(url_or_id: str) -> str:
    value = url_or_id.strip()

    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", value):
        return value

    parsed = urlparse(value)

    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
        if video_id:
            return video_id

    if parsed.hostname and "youtube.com" in parsed.hostname:
        query_video_id = parse_qs(parsed.query).get("v", [None])[0]
        if query_video_id:
            return query_video_id

        parts = [part for part in parsed.path.split("/") if part]
        if "shorts" in parts:
            index = parts.index("shorts")
            if index + 1 < len(parts):
                return parts[index + 1]

        if "embed" in parts:
            index = parts.index("embed")
            if index + 1 < len(parts):
                return parts[index + 1]

    raise ValueError("Invalid YouTube URL or video ID.")


def transcript_items_to_text(items) -> str:
    lines = []

    for item in items:
        if isinstance(item, dict):
            text = item.get("text", "")
            start = item.get("start")
        else:
            text = getattr(item, "text", "")
            start = getattr(item, "start", None)

        text = str(text).replace("\n", " ").strip()

        if not text:
            continue

        if start is not None:
            minute = int(float(start) // 60)
            second = int(float(start) % 60)
            lines.append(f"[{minute:02d}:{second:02d}] {text}")
        else:
            lines.append(text)

    return "\n".join(lines)


def load_youtube_transcript(url_or_id: str) -> dict:
    video_id = extract_youtube_video_id(url_or_id)

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en", "en-US", "hi"])
        text = transcript_items_to_text(transcript)
    except AttributeError:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "hi"])
        text = transcript_items_to_text(transcript)
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as exc:
        raise ValueError(f"Transcript not available for this YouTube video: {type(exc).__name__}") from exc
    except Exception as exc:
        raise ValueError(f"Could not fetch YouTube transcript: {type(exc).__name__}") from exc

    if not text.strip():
        raise ValueError("Transcript was fetched but empty.")

    return {
        "video_id": video_id,
        "source_name": f"youtube_{video_id}",
        "text": f"YouTube video ID: {video_id}\nURL: https://www.youtube.com/watch?v={video_id}\n\nTranscript:\n{text}",
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
    }