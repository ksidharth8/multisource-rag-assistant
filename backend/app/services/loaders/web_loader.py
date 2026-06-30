import requests
from bs4 import BeautifulSoup

from app.config import get_settings


def load_website(url: str) -> str:
    settings = get_settings()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=(5, 15))
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()

    if "text/html" not in content_type and "text/plain" not in content_type:
        raise ValueError(f"Unsupported content type: {content_type}")

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "svg", "form", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    cleaned_lines = []
    seen = set()
    total_chars = 0

    for line in lines:
        if len(line) <= 2:
            continue

        normalized = " ".join(line.split())

        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned_lines.append(normalized)
        total_chars += len(normalized)

        if total_chars >= settings.max_source_chars:
            break

    final_text = "\n".join(cleaned_lines).strip()

    if not final_text:
        raise ValueError("Website loaded but no readable text was found.")

    final_text = final_text[: settings.max_source_chars]

    return f"Title: {title}\nURL: {url}\n\n{final_text}"