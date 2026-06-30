import requests
from bs4 import BeautifulSoup


def load_website(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=20)
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
    previous = None

    for line in lines:
        if line == previous:
            continue

        if len(line) <= 2:
            continue

        cleaned_lines.append(line)
        previous = line

    final_text = "\n".join(cleaned_lines).strip()

    if not final_text:
        raise ValueError("Website loaded but no readable text was found.")

    return f"Title: {title}\nURL: {url}\n\n{final_text}"