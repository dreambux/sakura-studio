from __future__ import annotations

import random
import unicodedata

import pytest

from voice_machine.textsplit import normalize_text, split_sentences, split_text


def test_single_sentence_is_one_chunk() -> None:
    assert split_text("To jest jedno zdanie.", 200) == ["To jest jedno zdanie."]


def test_splits_on_sentence_boundaries() -> None:
    text = "Pierwsze zdanie jest dość długie. Drugie zdanie też. Trzecie kończy wypowiedź!"
    assert split_text(text, 200, min_chunk_chars=0) == [
        "Pierwsze zdanie jest dość długie.",
        "Drugie zdanie też.",
        "Trzecie kończy wypowiedź!",
    ]


def test_does_not_split_decimals_or_lowercase_continuation() -> None:
    assert split_sentences("Pi to około 3.14 w przybliżeniu.") == ["Pi to około 3.14 w przybliżeniu."]
    assert split_sentences("Zobacz np. kolejny przykład.") == ["Zobacz np. kolejny przykład."]


def test_splits_after_ellipsis_and_quotes() -> None:
    assert split_sentences('Powiedział "dość…" Potem wyszedł.') == ['Powiedział "dość…"', "Potem wyszedł."]


def test_tiny_sentences_are_merged_up_to_the_limit() -> None:
    chunks = split_text("Tak. Nie. Może. Jasne.", 200)
    assert chunks == ["Tak. Nie. Może. Jasne."]


def test_long_sentence_is_cut_at_clauses_within_limit() -> None:
    text = ", ".join(f"fragment numer {i}" for i in range(30)) + "."
    chunks = split_text(text, 80)
    assert len(chunks) > 1
    assert all(0 < len(c) <= 80 for c in chunks)


def test_text_without_spaces_is_hard_cut() -> None:
    chunks = split_text("a" * 500, 100)
    assert [len(c) for c in chunks] == [100] * 5


def test_control_characters_and_blank_input() -> None:
    assert split_text("   \n\t  \r\n ", 100) == []
    assert normalize_text("a\x00b​c\n\n d  e ") == ["a b c", "d e"]


def test_rejects_tiny_limit() -> None:
    with pytest.raises(ValueError):
        split_text("abc", 10)


def _strip(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace() and unicodedata.category(ch) not in ("Cc", "Cf", "Zl", "Zp"))


def test_invariants_on_random_text() -> None:
    rng = random.Random(1234)
    words = ["ala", "ma", "kota", "Zażółć", "gęślą", "jaźń", "3.14", "np.", "OK", "…", "?!", "„cytat”", "x" * 40]
    seps = [" ", "  ", ", ", ". ", "! ", "? ", "\n", " — ", "; "]
    for _ in range(300):
        text = "".join(rng.choice(words) + rng.choice(seps) for _ in range(rng.randint(0, 60)))
        limit = rng.choice([20, 35, 80, 200])
        chunks = split_text(text, limit)
        assert all(0 < len(c) <= limit for c in chunks)
        assert _strip("".join(chunks)) == _strip(text)
