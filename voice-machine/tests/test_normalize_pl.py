from __future__ import annotations

import random
import re

import pytest

from voice_machine.normalize_pl import (
    cardinal,
    inflect_ordinal,
    normalize_for_speech,
    normalize_pl,
    ordinal_phrase,
    plural_form,
)

CARDINALS = {
    0: "zero", 1: "jeden", 2: "dwa", 10: "dziesięć", 11: "jedenaście", 14: "czternaście", 19: "dziewiętnaście",
    20: "dwadzieścia", 21: "dwadzieścia jeden", 99: "dziewięćdziesiąt dziewięć", 100: "sto", 101: "sto jeden",
    110: "sto dziesięć", 200: "dwieście", 999: "dziewięćset dziewięćdziesiąt dziewięć", 1000: "tysiąc",
    1001: "tysiąc jeden", 2000: "dwa tysiące", 5000: "pięć tysięcy", 12000: "dwanaście tysięcy",
    21000: "dwadzieścia jeden tysięcy", 22000: "dwadzieścia dwa tysiące", 100000: "sto tysięcy",
    1_000_000: "milion", 2_000_000: "dwa miliony", 5_000_000: "pięć milionów", 1_000_000_000: "miliard",
    2026: "dwa tysiące dwadzieścia sześć", 1250: "tysiąc dwieście pięćdziesiąt",
    1_001_000: "milion tysiąc", -5: "minus pięć",
}


@pytest.mark.parametrize("n, words", CARDINALS.items())
def test_cardinals(n: int, words: str) -> None:
    assert cardinal(n) == words


def test_cardinals_match_num2words_oracle() -> None:
    num2words = pytest.importorskip("num2words").num2words
    for n in range(0, 30_000):
        assert cardinal(n) == num2words(n, lang="pl"), n
    rng = random.Random(7)
    for _ in range(3000):
        n = rng.randrange(0, 10**15)
        assert cardinal(n) == num2words(n, lang="pl"), n


def test_plural_form() -> None:
    forms = ("złoty", "złote", "złotych")
    expected = {0: "złotych", 1: "złoty", 2: "złote", 4: "złote", 5: "złotych", 12: "złotych", 14: "złotych", 21: "złotych", 22: "złote", 112: "złotych", 122: "złote"}
    for n, form in expected.items():
        assert plural_form(n, *forms) == form, n


@pytest.mark.parametrize(
    "n, case, gender, expected",
    [
        (1, "gen", "m", "pierwszego"), (2, "gen", "m", "drugiego"), (3, "loc", "m", "trzecim"),
        (6, "loc", "m", "szóstym"), (21, "gen", "m", "dwudziestego pierwszego"), (100, "nom", "m", "setny"),
        (121, "nom", "m", "sto dwudziesty pierwszy"), (2026, "loc", "m", "dwa tysiące dwudziestym szóstym"),
        (2026, "gen", "m", "dwa tysiące dwudziestego szóstego"), (2000, "gen", "m", "dwutysięcznego"),
        (1000, "nom", "m", "tysięczny"), (1900, "nom", "m", "tysiąc dziewięćsetny"), (2100, "nom", "m", "dwa tysiące setny"),
        (14, "nom", "f", "czternasta"), (3, "gen", "f", "trzeciej"), (2, "acc", "f", "drugą"), (3, "nom", "f", "trzecia"),
        (21, "nom", "f", "dwudziesta pierwsza"),
    ],
)
def test_ordinals(n: int, case: str, gender: str, expected: str) -> None:
    assert ordinal_phrase(n, case, gender) == expected


def test_inflect_special_stems() -> None:
    assert inflect_ordinal("drugi", "dat") == "drugiemu"
    assert inflect_ordinal("trzeci", "instr") == "trzecim"
    assert inflect_ordinal("piąty", "gen", "m") == "piątego"


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("3,14", "trzy przecinek czternaście"),
        ("0,05", "zero przecinek zero pięć"),
        ("0,5", "zero przecinek pięć"),
        ("1,2345", "jeden przecinek dwa trzy cztery pięć"),
        ("10,75", "dziesięć przecinek siedemdziesiąt pięć"),
        ("007", "zero zero siedem"),
        ("1 250 000", "milion dwieście pięćdziesiąt tysięcy"),
        ("12.345.678", "dwanaście milionów trzysta czterdzieści pięć tysięcy sześćset siedemdziesiąt osiem"),
        ("123 456 789", "sto dwadzieścia trzy miliony czterysta pięćdziesiąt sześć tysięcy siedemset osiemdziesiąt dziewięć"),
        ("-5", "minus pięć"),
        ("temperatura -5 stopni", "temperatura minus pięć stopni"),
        ("Windows 11", "Windows jedenaście"),
        ("COVID-19", "COVID-dziewiętnaście"),
        ("mp3 i A4", "mp3 i A4"),
    ],
)
def test_plain_numbers(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("5%", "pięć procent"),
        ("2,5%", "dwa przecinek pięć procent"),
        ("Wzrost o 100 %.", "Wzrost o sto procent."),
    ],
)
def test_percent(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("1 zł", "jeden złoty"),
        ("2 zł", "dwa złote"),
        ("5 zł", "pięć złotych"),
        ("22 zł", "dwadzieścia dwa złote"),
        ("25 zł", "dwadzieścia pięć złotych"),
        ("1250 zł", "tysiąc dwieście pięćdziesiąt złotych"),
        ("2000 zł", "dwa tysiące złotych"),
        ("12,50 zł", "dwanaście złotych pięćdziesiąt groszy"),
        ("12,5 zł", "dwanaście złotych pięćdziesiąt groszy"),
        ("1,01 zł", "jeden złoty jeden grosz"),
        ("0,99 zł", "dziewięćdziesiąt dziewięć groszy"),
        ("1 250,00 zł", "tysiąc dwieście pięćdziesiąt złotych"),
        ("1.250,50 zł", "tysiąc dwieście pięćdziesiąt złotych pięćdziesiąt groszy"),
        ("100 PLN", "sto złotych"),
        ("10 €", "dziesięć euro"),
        ("€10", "dziesięć euro"),
        ("$5", "pięć dolarów"),
        ("1 USD", "jeden dolar"),
        ("3 EUR", "trzy euro"),
        ("-5 zł", "minus pięć złotych"),
        ("5 mln zł", "pięć milionów złotych"),
        ("2 mld zł", "dwa miliardy złotych"),
        ("2,5 mln", "dwa przecinek pięć miliona"),
        ("1 mld", "jeden miliard"),
        ("3 tys. osób", "trzy tysiące osób"),
    ],
)
def test_currency_and_scales(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("5 km", "pięć kilometrów"),
        ("1 km", "jeden kilometr"),
        ("2 km", "dwa kilometry"),
        ("21 km", "dwadzieścia jeden kilometrów"),
        ("2,5 km", "dwa przecinek pięć kilometra"),
        ("70 kg", "siedemdziesiąt kilogramów"),
        ("36,6 °C", "trzydzieści sześć przecinek sześć stopnia Celsjusza"),
        ("20°C", "dwadzieścia stopni Celsjusza"),
        ("1°C", "jeden stopień Celsjusza"),
        ("2 °C", "dwa stopnie Celsjusza"),
        ("10 min", "dziesięć minut"),
        ("500 ml", "pięćset mililitrów"),
        ("3 l", "trzy litry"),
    ],
)
def test_units(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("19.11.2026", "dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku"),
        ("1.01.2000", "pierwszego stycznia dwutysięcznego roku"),
        ("Data: 31.12.1999 r. była ostatnia.", "Data: trzydziestego pierwszego grudnia tysiąc dziewięćset dziewięćdziesiątego dziewiątego roku była ostatnia."),
        ("Było to 5.05.2021 r.", "Było to piątego maja dwa tysiące dwudziestego pierwszego roku."),
        ("5 maja 2021 r. była", "piątego maja dwa tysiące dwudziestego pierwszego roku była"),
        ("19 listopada 2026", "dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku"),
        ("ISO 2026-11-19", "ISO dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku"),
        ("Spotkanie 3 marca.", "Spotkanie trzeciego marca."),
        ("Stało się w 2026 r. dzięki nam", "Stało się w dwa tysiące dwudziestym szóstym roku dzięki nam"),
        ("Stało się w 2026 r. Potem", "Stało się w dwa tysiące dwudziestym szóstym roku. Potem"),
        ("do 2030 r. wszystko", "do dwa tysiące trzydziestego roku wszystko"),
        ("od 1999 r. nic", "od tysiąc dziewięćset dziewięćdziesiątego dziewiątego roku nic"),
        ("2025 r. był", "dwa tysiące dwudziesty piąty rok był"),
        ("w 2000 r. coś", "w dwutysięcznym roku coś"),
        ("przed 2010 r. tak", "przed dwa tysiące dziesiątym rokiem tak"),
        ("rok 2026", "rok dwa tysiące dwudziesty szósty"),
        ("roku 2026", "roku dwa tysiące dwudziestego szóstego"),
        ("w XX wieku", "w dwudziestym wieku"),
        ("XXI wiek", "dwudziesty pierwszy wiek"),
        ("do XIX w. się", "do dziewiętnastego wieku się"),
    ],
)
def test_dates_years_centuries(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("14:30", "czternasta trzydzieści"),
        ("o 14:30", "o czternastej trzydzieści"),
        ("do 9:05", "do dziewiątej zero pięć"),
        ("o 12:00", "o dwunastej"),
        ("21:15", "dwudziesta pierwsza piętnaście"),
        ("o 22:00", "o dwudziestej drugiej"),
        ("na 8:00", "na ósmą"),
        ("o godz. 14:30", "o godzinie czternastej trzydzieści"),
        ("godz. 8:15", "godzina ósma piętnaście"),
        ("00:15", "zero piętnaście"),
        ("wynik 3:2", "wynik trzy:dwa"),
    ],
)
def test_times(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "source, spoken",
    [
        ("np. kot", "na przykład kot"),
        ("np. Kowalski", "na przykład Kowalski"),
        ("i inne m.in. psy", "i inne między innymi psy"),
        ("koty itd.", "koty i tak dalej."),
        ("koty itp. Potem", "koty i tym podobne. Potem"),
        ("itd. dalej", "i tak dalej dalej"),
        ("ok. 5 km", "około pięć kilometrów"),
        ("wg mnie", "według mnie"),
        ("Tom & Jerry", "Tom i Jerry"),
        ("2+2=4", "dwa plus dwa równa się cztery"),
        ("+48 123 456 789", "plus czterdzieści osiem, jeden dwa trzy, cztery pięć sześć, siedem osiem dziewięć"),
        ("tel. 123-456-789", "tel. jeden dwa trzy, cztery pięć sześć, siedem osiem dziewięć"),
    ],
)
def test_abbreviations_symbols_phones(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


def test_the_sample_sentence_shown_in_the_page() -> None:
    source = "Cześć! To jest Maszyna Głosów. Dziś jest 19 listopada 2026 roku, a w portfelu mam 1250 zł. Do zobaczenia o 14:30!"
    assert normalize_pl(source) == (
        "Cześć! To jest Maszyna Głosów. Dziś jest dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku, "
        "a w portfelu mam tysiąc dwieście pięćdziesiąt złotych. Do zobaczenia o czternastej trzydzieści!"
    )


def test_idempotent_and_digit_free_on_realistic_text() -> None:
    samples = [
        "W 2026 r. wydaliśmy 1 250,50 zł na 12 km trasy, o godz. 14:30, czyli ok. 5% budżetu.",
        "Tel. +48 600 700 800, e-mail w XXI wieku to norma; 3 tys. osób, 2,5 mln zł, 36,6 °C.",
        "Dnia 1.02.2020 r. oraz 3 marca 2021 odbyło się 7 spotkań (np. o 9:05).",
    ]
    for text in samples:
        once = normalize_pl(text)
        assert not re.search(r"\d", once), once
        assert normalize_pl(once) == once


def test_invalid_dates_do_not_crash_and_other_languages_are_untouched() -> None:
    normalize_pl("32.13.2026 i 00.00.0000 oraz 99:99")
    assert normalize_for_speech("To kosztuje 5 zł", "en") == "To kosztuje 5 zł"
    assert normalize_for_speech("To kosztuje 5 zł", "pl-PL") == "To kosztuje pięć złotych"
    assert normalize_for_speech("To kosztuje 5 zł", "PL") == "To kosztuje pięć złotych"


def test_huge_and_odd_numbers_fall_back_to_digits() -> None:
    assert normalize_pl("1" + "0" * 30) == "jeden " + " ".join(["zero"] * 30)
    assert normalize_pl("") == ""
    assert normalize_pl("  \n  ") == ""


def test_multiline_text_keeps_paragraph_breaks() -> None:
    assert normalize_pl("Pierwszy 1.\n\nDrugi 2.") == "Pierwszy jeden.\n\nDrugi dwa."
