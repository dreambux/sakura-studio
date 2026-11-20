"""Dzielenie tekstu na fragmenty do syntezy. Czysta funkcja, bez zależności od silnika."""

from __future__ import annotations

import re
import unicodedata

_SENTENCE_END = ".!?…"
_CLOSERS = "\"'”’)]»"
_OPENERS = "\"'„“(«["
_CLAUSE_BREAKS = ",;:—–"
# Znaki niewidoczne wewnątrz słów (z PDF, Worda, stron WWW): usuwamy bez śladu, bo zamiana na spację rozcina wyrazy ("nie­prawdopodobnie").
_INVISIBLE_INSIDE_WORDS = frozenset("\u00ad\u2060\u200c\u200d\ufeff\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
# Skróty, po których kropka nie kończy zdania, nawet gdy dalej stoi wielka litera ("ul. Długa", "prof. Kowalski", "św. Jana").
_NON_TERMINAL_ABBREVIATIONS = frozenset((
    "ul al pl os prof dr hab mgr inż ks św im tzw gen płk kpt mjr ppor doc red wyd nr str godz tel ok np art ust pkt "
    "rys tab zob por dyr ob wsp sp zm"
).split())
# Po tych znakach scalane linie nie wymagają dodatkowego przecinka.
_PUNCTUATION_BEFORE_JOIN = ".!?…,;:—–"
_RE_TRAILING_WORD = re.compile(r"([^\W\d_]+)$")


def normalize_text(text: str) -> list[str]:
    """Zwraca niepuste akapity: bez znaków sterujących, ze zbitymi odstępami."""
    cleaned = []
    for ch in text.replace("\r\n", "\n").replace("\r", "\n"):
        if ch == "\n":
            cleaned.append(ch)
        elif ch in _INVISIBLE_INSIDE_WORDS:
            continue
        elif unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp"):
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    lines = ("".join(cleaned)).split("\n")
    return [" ".join(line.split()) for line in lines if line.strip()]


def _ends_with_abbreviation(paragraph: str, dot_index: int) -> bool:
    """Czy kropka na pozycji dot_index należy do skrótu (ul., prof., św.) albo do inicjału (J. K. Rowling)."""
    found = _RE_TRAILING_WORD.search(paragraph[:dot_index])
    if not found:
        return False
    word = found.group(1)
    start = found.start(1)
    if start > 0 and paragraph[start - 1] not in " \t(\"„“'":
        return False
    return word.lower() in _NON_TERMINAL_ABBREVIATIONS or (len(word) == 1 and word.isupper())


def split_sentences(paragraph: str) -> list[str]:
    """Dzieli po . ! ? … gdy następne słowo zaczyna się wielką literą lub cyfrą (z wyjątkiem skrótów typu "ul.", "prof.")."""
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
                if m < n and (paragraph[m].isupper() or paragraph[m].isdigit()) and not (
                    paragraph[i] == "." and j == i + 1 and _ends_with_abbreviation(paragraph, i)
                ):
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


def _join(first: tuple[str, int], second: tuple[str, int]) -> str:
    """Skleja krótki fragment z następnym. Linie z różnych akapitów (lista, nagłówek) dostają przecinek, żeby nie zlały się
    w jeden oddech; to jedyny znak, który ta funkcja dodaje do tekstu."""
    left, right = first[0], second[0]
    if first[1] == second[1] or left[-1] in _PUNCTUATION_BEFORE_JOIN:
        return f"{left} {right}"
    return f"{left}, {right}"


def split_text(text: str, max_chars: int, *, min_chunk_chars: int = 24) -> list[str]:
    """Fragmenty o długości <= max_chars. Zachowuje wszystkie znaki niebiałe w kolejności; jedyny dodany znak to przecinek
    między krótkimi liniami z różnych akapitów."""
    if max_chars < 20:
        raise ValueError("max_chars must be at least 20")
    chunks: list[tuple[str, int]] = []
    for index, paragraph in enumerate(normalize_text(text)):
        for sentence in split_sentences(paragraph):
            for piece in [sentence] if len(sentence) <= max_chars else _split_long(sentence, max_chars):
                chunks.append((piece, index))
    merged: list[tuple[str, int]] = []
    for chunk, index in chunks:
        if merged and len(merged[-1][0]) < min_chunk_chars:
            joined = _join(merged[-1], (chunk, index))
            if len(joined) <= max_chars:
                merged[-1] = (joined, index)
                continue
        merged.append((chunk, index))
    if len(merged) >= 2 and len(merged[-1][0]) < min_chunk_chars:
        joined = _join(merged[-2], merged[-1])
        if len(joined) <= max_chars:
            merged.pop()
            merged[-1] = (joined, merged[-1][1])
    return [chunk for chunk, _index in merged]
