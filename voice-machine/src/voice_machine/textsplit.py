"""Dzielenie tekstu na fragmenty do syntezy. Czysta funkcja, bez zależności od silnika."""

from __future__ import annotations

import unicodedata

_SENTENCE_END = ".!?…"
_CLOSERS = "\"'”’)]»"
_OPENERS = "\"'„“(«["
_CLAUSE_BREAKS = ",;:—–"


def normalize_text(text: str) -> list[str]:
    """Zwraca niepuste akapity: bez znaków sterujących, ze zbitymi odstępami."""
    cleaned = []
    for ch in text.replace("\r\n", "\n").replace("\r", "\n"):
        if ch == "\n":
            cleaned.append(ch)
        elif unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp"):
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    lines = ("".join(cleaned)).split("\n")
    return [" ".join(line.split()) for line in lines if line.strip()]


def split_sentences(paragraph: str) -> list[str]:
    """Dzieli po . ! ? … gdy następne słowo zaczyna się wielką literą lub cyfrą."""
    out: list[str] = []
    n = len(paragraph)
    start = 0
    i = 0
    while i < n:
        if paragraph[i] in _SENTENCE_END:
            j = i + 1
            while j < n and paragraph[j] in _SENTENCE_END:
                j += 1
            while j < n and paragraph[j] in _CLOSERS:
                j += 1
            k = j
            while k < n and paragraph[k].isspace():
                k += 1
            if k > j and k < n:
                m = k
                while m < n and paragraph[m] in _OPENERS:
                    m += 1
                if m < n and (paragraph[m].isupper() or paragraph[m].isdigit()):
                    piece = paragraph[start:j].strip()
                    if piece:
                        out.append(piece)
                    start = k
                    i = k
                    continue
            i = j
            continue
        i += 1
    tail = paragraph[start:].strip()
    if tail:
        out.append(tail)
    return out


def _split_long(sentence: str, max_chars: int) -> list[str]:
    parts: list[str] = []
    rest = sentence.strip()
    floor = max_chars // 3
    while len(rest) > max_chars:
        window = rest[:max_chars]
        clause = max(window.rfind(c) for c in _CLAUSE_BREAKS)
        if clause >= floor:
            cut = clause + 1
        else:
            space = window.rfind(" ")
            cut = space if space >= floor else max_chars
        head = rest[:cut].strip()
        rest = rest[cut:].strip()
        if head:
            parts.append(head)
    if rest:
        parts.append(rest)
    return parts


def split_text(text: str, max_chars: int, *, min_chunk_chars: int = 24) -> list[str]:
    """Fragmenty o długości <= max_chars. Zachowuje wszystkie znaki niebiałe w kolejności."""
    if max_chars < 20:
        raise ValueError("max_chars must be at least 20")
    chunks: list[str] = []
    for paragraph in normalize_text(text):
        for sentence in split_sentences(paragraph):
            if len(sentence) <= max_chars:
                chunks.append(sentence)
            else:
                chunks.extend(_split_long(sentence, max_chars))
    merged: list[str] = []
    for chunk in chunks:
        if merged and len(merged[-1]) < min_chunk_chars and len(merged[-1]) + 1 + len(chunk) <= max_chars:
            merged[-1] = f"{merged[-1]} {chunk}"
        else:
            merged.append(chunk)
    if len(merged) >= 2 and len(merged[-1]) < min_chunk_chars and len(merged[-2]) + 1 + len(merged[-1]) <= max_chars:
        tail = merged.pop()
        merged[-1] = f"{merged[-1]} {tail}"
    return merged
