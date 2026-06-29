import requests
from bs4 import BeautifulSoup


def load_website(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 MultiSourceRAG/1.0"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "svg"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return f"Title: {title}\nURL: {url}\n\n" + "\n".join(lines)
