from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int


def chunk_text(
    text: str,
    chunk_size: int = 900,
    overlap: int = 120,
    max_chunks: int = 10,
) -> list[Chunk]:
    text = text.strip()

    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    n = len(text)

    while start < n and len(chunks) < max_chunks:
        end = min(start + chunk_size, n)
        window = text[start:end]

        if end < n:
            break_points = [
                window.rfind("\n\n"),
                window.rfind(". "),
                window.rfind("\n"),
                window.rfind(" "),
            ]

            valid_breaks = [bp for bp in break_points if bp > chunk_size * 0.55]
            cut = max(valid_breaks) if valid_breaks else -1

            if cut != -1:
                end = start + cut + 1
                window = text[start:end]

        cleaned = window.strip()

        if cleaned:
            chunks.append(Chunk(text=cleaned, index=len(chunks)))

        if end >= n:
            break

        start = max(0, end - overlap)

    return chunks