"""Normalizacja polskiego tekstu pod syntezę mowy. Czyste funkcje, bez zależności.

Zasada: rozwijamy tylko to, co da się rozwinąć poprawnie gramatycznie, a resztę zostawiamy bez zmian
zamiast zgadywać. Obsługiwane: liczebniki główne (mianownik), ułamki dziesiętne, procenty, waluty z odmianą
rzeczownika, skróty tys./mln/mld, jednostki, daty, lata i wieki z przypadkiem wybieranym po przyimku,
godziny, numery telefonów, kilka częstych skrótów i symboli.

Znane ograniczenie: liczba przy rzeczowniku w przypadku zależnym ("z pięcioma osobami") jest czytana
w mianowniku ("z pięć osobami"), bo bez analizy składniowej nie da się wybrać formy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --- liczebniki główne ------------------------------------------------------------------------------

_UNITS = ("zero", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć")
_TEENS = (
    "dziesięć", "jedenaście", "dwanaście", "trzynaście", "czternaście",
    "piętnaście", "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście",
)
_TENS = (
    "", "", "dwadzieścia", "trzydzieści", "czterdzieści",
    "pięćdziesiąt", "sześćdziesiąt", "siedemdziesiąt", "osiemdziesiąt", "dziewięćdziesiąt",
)
_HUNDREDS = ("", "sto", "dwieście", "trzysta", "czterysta", "pięćset", "sześćset", "siedemset", "osiemset", "dziewięćset")
# (mianownik l.poj., mianownik l.mn., dopełniacz l.mn., dopełniacz l.poj.)
_SCALES = (
    ("tysiąc", "tysiące", "tysięcy", "tysiąca"),
    ("milion", "miliony", "milionów", "miliona"),
    ("miliard", "miliardy", "miliardów", "miliarda"),
    ("bilion", "biliony", "bilionów", "biliona"),
    ("biliard", "biliardy", "biliardów", "biliarda"),
    ("trylion", "tryliony", "trylionów", "tryliona"),
)
MAX_CARDINAL = 10**21 - 1


def plural_form(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def _below_thousand(n: int) -> list[str]:
    words: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        words.append(_HUNDREDS[hundreds])
    if rest:
        if rest < 10:
            words.append(_UNITS[rest])
        elif rest < 20:
            words.append(_TEENS[rest - 10])
        else:
            tens, units = divmod(rest, 10)
            words.append(_TENS[tens])
            if units:
                words.append(_UNITS[units])
    return words


def cardinal(n: int) -> str:
    """Liczebnik główny w mianowniku: 2026 -> "dwa tysiące dwadzieścia sześć"."""
    if n < 0:
        return "minus " + cardinal(-n)
    if n == 0:
        return "zero"
    if n > MAX_CARDINAL:
        raise ValueError("number too large")
    groups: list[int] = []
    m = n
    while m:
        groups.append(m % 1000)
        m //= 1000
    words: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        group = groups[index]
        if group == 0:
            continue
        if index == 0:
            words.extend(_below_thousand(group))
        else:
            one, few, many, _gen = _SCALES[index - 1]
            if group != 1:
                words.extend(_below_thousand(group))
            words.append(plural_form(group, one, few, many))
    return " ".join(words)


def spell_digits(digits: str) -> str:
    return " ".join(_UNITS[int(c)] for c in digits if c.isdigit())


# --- liczebniki porządkowe i przypadki --------------------------------------------------------------

_ORD_UNITS = ("", "pierwszy", "drugi", "trzeci", "czwarty", "piąty", "szósty", "siódmy", "ósmy", "dziewiąty")
_ORD_TEENS = (
    "dziesiąty", "jedenasty", "dwunasty", "trzynasty", "czternasty",
    "piętnasty", "szesnasty", "siedemnasty", "osiemnasty", "dziewiętnasty",
)
_ORD_TENS = (
    "", "", "dwudziesty", "trzydziesty", "czterdziesty",
    "pięćdziesiąty", "sześćdziesiąty", "siedemdziesiąty", "osiemdziesiąty", "dziewięćdziesiąty",
)
_ORD_HUNDREDS = (
    "", "setny", "dwusetny", "trzysetny", "czterechsetny",
    "pięćsetny", "sześćsetny", "siedemsetny", "osiemsetny", "dziewięćsetny",
)
_ORD_THOUSANDS = {1: "tysięczny", 2: "dwutysięczny"}
MAX_ORDINAL = 2999


def _ordinal_words(n: int) -> list[tuple[str, bool]]:
    """(słowo, czy_porządkowe). W złożonych porządkowych tysiące i setki zostają głównymi, chyba że są ostatnie."""
    if not 1 <= n <= MAX_ORDINAL:
        raise ValueError("ordinal out of range")
    thousands, rest = divmod(n, 1000)
    if rest == 0:
        return [(_ORD_THOUSANDS[thousands], True)]
    out: list[tuple[str, bool]] = []
    if thousands == 1:
        out.append(("tysiąc", False))
    elif thousands == 2:
        out.extend([("dwa", False), ("tysiące", False)])
    hundreds, rem = divmod(rest, 100)
    if rem == 0:
        out.append((_ORD_HUNDREDS[hundreds], True))
        return out
    if hundreds:
        out.append((_HUNDREDS[hundreds], False))
    if rem < 10:
        out.append((_ORD_UNITS[rem], True))
    elif rem < 20:
        out.append((_ORD_TEENS[rem - 10], True))
    else:
        tens, units = divmod(rem, 10)
        out.append((_ORD_TENS[tens], True))
        if units:
            out.append((_ORD_UNITS[units], True))
    return out


_MASC_SPECIAL = {
    "drugi": {"gen": "drugiego", "dat": "drugiemu", "loc": "drugim", "instr": "drugim"},
    "trzeci": {"gen": "trzeciego", "dat": "trzeciemu", "loc": "trzecim", "instr": "trzecim"},
}
_MASC_ENDINGS = {"gen": "ego", "dat": "emu", "loc": "ym", "instr": "ym"}
_FEM_ENDINGS = {"nom": "a", "gen": "ej", "dat": "ej", "loc": "ej", "acc": "ą", "instr": "ą"}


def inflect_ordinal(word: str, case: str, gender: str = "m") -> str:
    """Odmiana przymiotnikowego liczebnika porządkowego (mianownik męski na wejściu)."""
    if gender == "m":
        if case in ("nom", "acc"):
            return word
        if word in _MASC_SPECIAL:
            return _MASC_SPECIAL[word][case]
        return word[:-1] + _MASC_ENDINGS[case]
    if word == "drugi":
        stem = "drugi" if case in ("gen", "dat", "loc") else "drug"  # druga, drugiej, drugą
    elif word == "trzeci":
        stem = "trzeci"
    else:
        stem = word[:-1]
    return stem + _FEM_ENDINGS[case]


def ordinal_phrase(n: int, case: str = "nom", gender: str = "m") -> str:
    return " ".join(inflect_ordinal(w, case, gender) if is_ord else w for w, is_ord in _ordinal_words(n))


_MONTHS_GEN = (
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
)
_MONTH_INDEX = {name: i + 1 for i, name in enumerate(_MONTHS_GEN)}

_NOUN_ROK = {"nom": "rok", "acc": "rok", "gen": "roku", "loc": "roku", "instr": "rokiem"}
_NOUN_WIEK = {"nom": "wiek", "acc": "wiek", "gen": "wieku", "loc": "wieku", "instr": "wiekiem"}
_NOUN_GODZINA = {"nom": "godzina", "gen": "godziny", "dat": "godzinie", "loc": "godzinie", "acc": "godzinę", "instr": "godziną"}

# Przypadek wybierany po przyimku. Brak przyimka albo nieznany przyimek: mianownik (= biernik rzeczowników nieżywotnych).
_PREP_CASE_DATE = {
    "w": "loc", "we": "loc", "po": "loc", "przy": "loc",
    "przed": "instr", "nad": "instr", "pod": "instr",
    "do": "gen", "od": "gen", "z": "gen", "ze": "gen", "około": "gen", "dla": "gen", "bez": "gen", "u": "gen", "podczas": "gen",
}
_PREP_CASE_TIME = {
    "o": "loc", "po": "loc", "w": "loc",
    "do": "gen", "od": "gen", "około": "gen", "z": "gen", "ze": "gen", "dla": "gen",
    "na": "acc", "za": "acc", "przez": "acc", "przed": "instr",
}


def _case_after(prep: str | None, table: dict[str, str]) -> str:
    return table.get(prep.strip().lower(), "nom") if prep else "nom"


def _roman_to_int(text: str) -> int | None:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(text):
        v = values[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total if _int_to_roman(total) == text else None


def _int_to_roman(n: int) -> str:
    out = []
    for value, symbol in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


# --- liczby w tekście --------------------------------------------------------------------------------

# Kolejność alternatyw ma znaczenie: najpierw formy z separatorami tysięcy.
_NUM_CORE = r"\d{1,3}(?:\.\d{3}){2,}(?:,\d+)?|\d{1,3}(?:\.\d{3})+,\d+|\d{1,3}(?: \d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?"
_NUM = rf"(?P<neg>(?<!\w)-)?(?<![\w.])(?P<num>{_NUM_CORE})(?!\w)"


@dataclass(frozen=True)
class _Num:
    neg: bool
    int_part: str
    frac: str | None


def _parse(token: str, neg: bool) -> _Num:
    t = token
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t) and (t.count(".") >= 2 or "," in t):
        t = t.replace(".", "")
    t = t.replace(" ", "")
    if "," in t:
        ip, fp = t.split(",", 1)
    elif "." in t:
        ip, fp = t.split(".", 1)
    else:
        ip, fp = t, None
    return _Num(neg, ip, fp)


def _say_int(ip: str) -> str:
    if (len(ip) > 1 and ip.startswith("0")) or int(ip) > MAX_CARDINAL:
        return spell_digits(ip)
    return cardinal(int(ip))


def _say_frac(fp: str) -> str:
    rest = fp.lstrip("0")
    lead = len(fp) - len(rest)
    if not rest:
        return " ".join(["zero"] * len(fp))
    if len(rest) <= 3:
        return " ".join(["zero"] * lead + [cardinal(int(rest))])
    return spell_digits(fp)


def say_number(p: _Num) -> str:
    text = _say_int(p.int_part)
    if p.frac is not None:
        text += " przecinek " + _say_frac(p.frac)
    return ("minus " if p.neg else "") + text


def _int_value(p: _Num) -> int | None:
    if len(p.int_part) > 1 and p.int_part.startswith("0"):
        return None
    value = int(p.int_part)
    return value if value <= MAX_CARDINAL else None


def _noun_for(p: _Num, forms: tuple[str, str, str, str]) -> str:
    """Forma rzeczownika po liczbie: forms = (1, 2-4, 5+, dopełniacz l.poj. dla ułamków)."""
    one, few, many, gen_sg = forms
    if p.frac is not None:
        return gen_sg
    value = _int_value(p)
    if value is None:
        return many
    if value >= 1000 and value % 1000 == 0:
        return many  # po słowie tysiąc/milion/miliard rzeczownik stoi w dopełniaczu l.mn.
    return plural_form(value, one, few, many)


def _sentence_dot(m: re.Match[str]) -> str:
    """Skrót z kropką mógł kończyć zdanie: oddajemy kropkę, jeśli dalej jest nowe zdanie albo koniec."""
    rest = m.string[m.end():].lstrip()
    return "." if (not rest or rest[0].isupper() or rest[0] in "„\"'(") else ""


# --- waluty, skróty skalowe, jednostki ----------------------------------------------------------------

_CURRENCY = {
    "zł": ("złoty", "złote", "złotych", "złotego"),
    "PLN": ("złoty", "złote", "złotych", "złotego"),
    "EUR": ("euro", "euro", "euro", "euro"),
    "€": ("euro", "euro", "euro", "euro"),
    "USD": ("dolar", "dolary", "dolarów", "dolara"),
    "$": ("dolar", "dolary", "dolarów", "dolara"),
    "GBP": ("funt", "funty", "funtów", "funta"),
    "£": ("funt", "funty", "funtów", "funta"),
}
_SUBUNIT = {
    "zł": ("grosz", "grosze", "groszy"), "PLN": ("grosz", "grosze", "groszy"),
    "EUR": ("cent", "centy", "centów"), "€": ("cent", "centy", "centów"),
    "USD": ("cent", "centy", "centów"), "$": ("cent", "centy", "centów"),
    "GBP": ("pens", "pensy", "pensów"), "£": ("pens", "pensy", "pensów"),
}
_SCALE_UNITS = {"tys.": _SCALES[0], "mln": _SCALES[1], "mld": _SCALES[2]}
_UNIT_FORMS = {
    "km": ("kilometr", "kilometry", "kilometrów", "kilometra"),
    "cm": ("centymetr", "centymetry", "centymetrów", "centymetra"),
    "mm": ("milimetr", "milimetry", "milimetrów", "milimetra"),
    "kg": ("kilogram", "kilogramy", "kilogramów", "kilograma"),
    "ml": ("mililitr", "mililitry", "mililitrów", "mililitra"),
    "min": ("minuta", "minuty", "minut", "minuty"),
    "m": ("metr", "metry", "metrów", "metra"),
    "g": ("gram", "gramy", "gramów", "grama"),
    "l": ("litr", "litry", "litrów", "litra"),
}
_DEGREE_FORMS = ("stopień", "stopnie", "stopni", "stopnia")


def say_currency(p: _Num, key: str) -> str:
    one, few, many, gen_sg = _CURRENCY[key]
    prefix = "minus " if p.neg else ""
    if p.frac is not None and len(p.frac) <= 2 and len(p.int_part) <= 15:
        minor = int(p.frac.ljust(2, "0"))
        major_value = int(p.int_part)
        parts: list[str] = []
        if major_value or not minor:
            parts.append(f"{cardinal(major_value)} {_noun_for(_Num(False, p.int_part, None), (one, few, many, gen_sg))}")
        if minor:
            s_one, s_few, s_many = _SUBUNIT[key]
            parts.append(f"{cardinal(minor)} {plural_form(minor, s_one, s_few, s_many)}")
        return prefix + " ".join(parts)
    return f"{say_number(_Num(p.neg, p.int_part, p.frac))} {_noun_for(p, (one, few, many, gen_sg))}"


# --- kroki normalizacji ------------------------------------------------------------------------------

_MONTH_ALT = "|".join(_MONTHS_GEN)
_PREP_ALT_DATE = "|".join(sorted(_PREP_CASE_DATE, key=len, reverse=True))
_PREP_ALT_TIME = "|".join(sorted(_PREP_CASE_TIME, key=len, reverse=True))

_RE_PHONE_PLUS = re.compile(r"(?<![\w])\+(\d{2})[ -]?(\d{3})[ -]?(\d{3})[ -]?(\d{3})(?!\w)")
_RE_PHONE_TEL = re.compile(r"(?P<pre>\btel\.?\s*:?\s*)(\d{3})[ -]?(\d{3})[ -]?(\d{3})(?!\w)", re.IGNORECASE)
_RE_DATE_ISO = re.compile(r"(?<![\w./:-])(\d{4})-(\d{2})-(\d{2})(?![\w-])")
_RE_DATE_NUM = re.compile(r"(?<![\w./:-])(\d{1,2})([./-])(\d{1,2})\2(\d{4})(?!\w)(?P<r>\s*(?:r\.|roku)(?!\w))?")
_RE_DATE_TEXT = re.compile(rf"(?<!\w)(\d{{1,2}})\s+({_MONTH_ALT})(?:\s+(\d{{4}}))?(?!\w)(?P<r>\s*(?:r\.|roku)(?!\w))?", re.IGNORECASE)
_RE_YEAR_R = re.compile(rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DATE})\s+)?(?<![\w.])(?P<year>\d{{4}})\s*(?P<r>r\.|roku)(?!\w)", re.IGNORECASE)
_RE_YEAR_NOUN = re.compile(r"(?<!\w)(?P<noun>rok|roku|rokiem)\s+(?P<year>\d{4})(?![\w.,]?\d)", re.IGNORECASE)
_RE_ROMAN = re.compile(rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DATE})\s+)?(?<![\w])(?P<roman>[IVXLC]{{1,6}})\s+(?P<noun>wiek(?:u|iem)?|w\.)(?!\w)")
_RE_TIME = re.compile(rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_TIME})\s+)?(?P<g>godz\.\s*)?(?<![\w:.,])(?P<h>[01]?\d|2[0-3]):(?P<m>[0-5]\d)(?![\w:])", re.IGNORECASE)
_RE_PERCENT = re.compile(_NUM + r"\s*%")
_RE_CUR_SCALE = re.compile(_NUM + r"\s*(?P<scale>tys\.|mln|mld)\s*(?P<cur>zł|PLN|EUR|USD|GBP|€|\$|£)(?!\w)")
_RE_SCALE = re.compile(_NUM + r"\s*(?P<scale>tys\.|mln|mld)(?!\w)")
_RE_CUR_SUFFIX = re.compile(_NUM + r"\s*(?P<cur>zł|PLN|EUR|USD|GBP|€|\$|£)(?!\w)")
_RE_CUR_PREFIX = re.compile(rf"(?P<cur>[€$£])\s*{_NUM}")
_RE_DEGREES = re.compile(_NUM + r"\s*°\s*C(?!\w)")
_RE_UNIT = re.compile(_NUM + r"\s?(?P<unit>km|cm|mm|kg|ml|min|m|g|l)(?!\w)")
_RE_NUMBER = re.compile(_NUM)

# (wzorzec, rozwinięcie, czy skrót często kończy zdanie). Tylko "itd." i "itp." kończą zdania; po "np. Kowalski" kropka nie jest końcem.
_ABBREVIATIONS = (
    (re.compile(r"(?<!\w)np\."), "na przykład", False),
    (re.compile(r"(?<!\w)m\.in\."), "między innymi", False),
    (re.compile(r"(?<!\w)itd\."), "i tak dalej", True),
    (re.compile(r"(?<!\w)itp\."), "i tym podobne", True),
    (re.compile(r"(?<!\w)tzn\."), "to znaczy", False),
    (re.compile(r"(?<!\w)tj\."), "to jest", False),
    (re.compile(r"(?<!\w)wg(?!\w)\.?"), "według", False),
)
# "ok." przed liczbą to "około"; sprawdzamy to przed rozwinięciem cyfr.
_RE_OKOLO = re.compile(r"(?<!\w)ok\.(?=\s*\d)")


def _num_from(m: re.Match[str]) -> _Num:
    return _parse(m.group("num"), bool(m.group("neg")))


def _step_phones(s: str) -> str:
    def plus(m: re.Match[str]) -> str:
        groups = ", ".join(spell_digits(m.group(i)) for i in (2, 3, 4))
        return f"plus {cardinal(int(m.group(1)))}, {groups}"

    def tel(m: re.Match[str]) -> str:
        return m.group("pre") + ", ".join(spell_digits(m.group(i)) for i in (2, 3, 4))

    return _RE_PHONE_TEL.sub(tel, _RE_PHONE_PLUS.sub(plus, s))


def _date_phrase(day: int, month: int, year: int | None) -> str | None:
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    text = f"{ordinal_phrase(day, 'gen')} {_MONTHS_GEN[month - 1]}"
    if year is not None:
        if not 1000 <= year <= MAX_ORDINAL:
            return None
        text += f" {ordinal_phrase(year, 'gen')} roku"
    return text


def _step_dates(s: str) -> str:
    def iso(m: re.Match[str]) -> str:
        return _date_phrase(int(m.group(3)), int(m.group(2)), int(m.group(1))) or m.group(0)

    def numeric(m: re.Match[str]) -> str:
        phrase = _date_phrase(int(m.group(1)), int(m.group(3)), int(m.group(4)))
        if phrase is None:
            return m.group(0)
        return phrase + (_sentence_dot(m) if m.group("r") and m.group("r").rstrip().endswith(".") else "")

    def textual(m: re.Match[str]) -> str:
        year = int(m.group(3)) if m.group(3) else None
        phrase = _date_phrase(int(m.group(1)), _MONTH_INDEX[m.group(2).lower()], year)
        if phrase is None:
            return m.group(0)
        if m.group("r") and year is None:
            return m.group(0)
        return phrase + (_sentence_dot(m) if m.group("r") and m.group("r").rstrip().endswith(".") else "")

    s = _RE_DATE_ISO.sub(iso, s)
    s = _RE_DATE_NUM.sub(numeric, s)
    return _RE_DATE_TEXT.sub(textual, s)


def _step_years(s: str) -> str:
    def with_r(m: re.Match[str]) -> str:
        year = int(m.group("year"))
        if not 1000 <= year <= MAX_ORDINAL:
            return m.group(0)
        prep = m.group("prep") or ""
        case = _case_after(m.group("prep"), _PREP_CASE_DATE)
        dot = _sentence_dot(m) if m.group("r").endswith(".") else ""
        return f"{prep}{ordinal_phrase(year, case)} {_NOUN_ROK[case]}{dot}"

    def after_noun(m: re.Match[str]) -> str:
        year = int(m.group("year"))
        if not 1000 <= year <= MAX_ORDINAL:
            return m.group(0)
        noun = m.group("noun").lower()
        case = {"rok": "nom", "roku": "gen", "rokiem": "instr"}[noun]
        return f"{m.group('noun')} {ordinal_phrase(year, case)}"

    return _RE_YEAR_NOUN.sub(after_noun, _RE_YEAR_R.sub(with_r, s))


def _step_roman(s: str) -> str:
    def sub(m: re.Match[str]) -> str:
        n = _roman_to_int(m.group("roman"))
        if n is None or not 1 <= n <= 30:
            return m.group(0)
        prep = m.group("prep") or ""
        noun = m.group("noun")
        if noun == "wiek":
            case = "nom"
        elif noun == "wieku":
            case = _case_after(m.group("prep"), _PREP_CASE_DATE)
            case = case if case in ("loc", "gen") else "gen"
        elif noun == "wiekiem":
            case = "instr"
        else:  # skrót "w."
            case = _case_after(m.group("prep"), _PREP_CASE_DATE)
        dot = _sentence_dot(m) if noun == "w." else ""
        return f"{prep}{ordinal_phrase(n, case)} {_NOUN_WIEK[case]}{dot}"

    return _RE_ROMAN.sub(sub, s)


def _step_times(s: str) -> str:
    def sub(m: re.Match[str]) -> str:
        hour, minute = int(m.group("h")), int(m.group("m"))
        prep = m.group("prep") or ""
        case = _case_after(m.group("prep"), _PREP_CASE_TIME)
        prefix = prep
        if m.group("g"):
            noun_case = "loc" if prep.strip().lower() == "o" else case
            prefix += _NOUN_GODZINA[noun_case] + " "
        hour_words = "zero" if hour == 0 else ordinal_phrase(hour, case, "f")
        if minute == 0:
            minutes = ""
        elif minute < 10:
            minutes = f" zero {_UNITS[minute]}"
        else:
            minutes = " " + cardinal(minute)
        return prefix + hour_words + minutes

    return _RE_TIME.sub(sub, s)


def _step_numbers(s: str) -> str:
    s = _RE_PERCENT.sub(lambda m: f"{say_number(_num_from(m))} procent", s)

    def scale_text(p: _Num, key: str) -> str:
        one, few, many, gen_sg = _SCALE_UNITS[key]
        return f"{say_number(p)} {_noun_for(p, (one, few, many, gen_sg))}"

    def cur_scale(m: re.Match[str]) -> str:
        p = _num_from(m)
        noun = _CURRENCY[m.group("cur")][2]
        return f"{scale_text(p, m.group('scale'))} {noun}"

    def only_scale(m: re.Match[str]) -> str:
        dot = _sentence_dot(m) if m.group("scale").endswith(".") else ""
        return scale_text(_num_from(m), m.group("scale")) + dot

    s = _RE_CUR_SCALE.sub(cur_scale, s)
    s = _RE_SCALE.sub(only_scale, s)
    s = _RE_CUR_SUFFIX.sub(lambda m: say_currency(_num_from(m), m.group("cur")), s)
    s = _RE_CUR_PREFIX.sub(lambda m: say_currency(_num_from(m), m.group("cur")), s)
    s = _RE_DEGREES.sub(lambda m: f"{say_number(_num_from(m))} {_noun_for(_num_from(m), _DEGREE_FORMS)} Celsjusza", s)
    s = _RE_UNIT.sub(lambda m: f"{say_number(_num_from(m))} {_noun_for(_num_from(m), _UNIT_FORMS[m.group('unit')])}", s)
    return _RE_NUMBER.sub(lambda m: say_number(_num_from(m)), s)


def _step_abbreviations(s: str) -> str:
    for pattern, replacement, can_end_sentence in _ABBREVIATIONS:
        def sub(m: re.Match[str], replacement: str = replacement, can_end: bool = can_end_sentence) -> str:
            return replacement + (_sentence_dot(m) if can_end else "")

        s = pattern.sub(sub, s)
    return s


def _step_symbols(s: str) -> str:
    s = re.sub(r"\s*&\s*", " i ", s)
    s = re.sub(r"\+", " plus ", s)
    return re.sub(r"\s*=\s*", " równa się ", s)


def normalize_pl(text: str) -> str:
    """Rozwija liczby, daty, godziny, waluty i częste skróty na słowa gotowe do wypowiedzenia."""
    s = text.replace(" ", " ").replace(" ", " ").replace(" ", " ").replace("−", "-")
    s = _RE_OKOLO.sub("około", s)
    for step in (_step_phones, _step_dates, _step_years, _step_roman, _step_times, _step_numbers, _step_abbreviations, _step_symbols):
        s = step(s)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.split("\n")]
    return "\n".join(lines).strip()


def normalize_for_speech(text: str, language: str) -> str:
    """Normalizacja zależna od języka. Dla innych języków niż polski tekst zostaje bez zmian."""
    return normalize_pl(text) if language.lower().split("-")[0] == "pl" else text
