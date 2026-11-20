"""Normalizacja polskiego tekstu pod syntezę mowy. Czyste funkcje, bez zależności.

Zasada: rozwijamy tylko to, co da się rozwinąć poprawnie gramatycznie, a resztę zostawiamy bez zmian
zamiast zgadywać. Obsługiwane: liczebniki główne (z rodzajem przy 1 i 2, gdy po liczbie stoi znany rzeczownik),
ułamki dziesiętne, procenty, waluty z odmianą rzeczownika, skróty tys./mln/mld, jednostki (także sklejone z liczbą,
złożone i kwadratowe), daty (także zakresy: "od 3 do 5 marca"), lata i wieki z przypadkiem wybieranym po przyimku,
godziny (także "godz. 19.30", północ), numery telefonów i długie ciągi cyfr, kilka częstych skrótów i symboli.
Adresy URL, e-maile, wzmianki Discorda i numery wersji zostają bez zmian albo są czytane znak po znaku.

Znane ograniczenia (bez analizy składniowej nie da się ich rozstrzygnąć):
- liczba przy rzeczowniku w przypadku zależnym ("z pięcioma osobami") jest czytana w mianowniku;
- rodzaj 1 i 2 wybieramy z małego słownika częstych rzeczowników (_FEM_NOUNS, _NEUT_SG); nieznany rzeczownik dostaje
  rodzaj męski ("dwa nieznanerzeczy");
- liczebniki porządkowe zapisane jako "1." czytamy jak liczebnik główny z kropką.
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


def _agree(words: str, n: int, gender: str) -> str:
    """Rodzaj liczebników 1 i 2 przy rzeczowniku żeńskim ("jedna", "dwie") i nijakim ("jedno"; "dwa" bez zmian)."""
    if gender == "m":
        return words
    head, sep, last = words.rpartition(" ")
    if n == 1 and last == "jeden":
        last = "jedna" if gender == "f" else "jedno"
    elif gender == "f" and last == "dwa":
        last = "dwie"  # także 22, 32, 102: ostatnie słowo "dwa" zawsze oznacza liczbę kończącą się na 2 (nie 12)
    return f"{head}{sep}{last}"


def cardinal(n: int, gender: str = "m") -> str:
    """Liczebnik główny w mianowniku: 2026 -> "dwa tysiące dwadzieścia sześć". gender: m, f albo n (tylko 1 i 2 się zmieniają)."""
    if n < 0:
        return "minus " + cardinal(-n, gender)
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
    return _agree(" ".join(words), n, gender)


def spell_digits(digits: str) -> str:
    return " ".join(_UNITS[int(c)] for c in digits if c.isdigit())


# --- rodzaj rzeczowników po liczebnikach 1 i 2 ----------------------------------------------------------
# Mały słownik (własny wybór, nie pełna fleksja): (mianownik l.poj., mianownik l.mn.). Po "1" sprawdzamy l.poj., po "2" l.mn.
_FEM_NOUNS = (
    ("osoba", "osoby"), ("godzina", "godziny"), ("minuta", "minuty"), ("sekunda", "sekundy"), ("doba", "doby"),
    ("nagroda", "nagrody"), ("wiadomość", "wiadomości"), ("piosenka", "piosenki"), ("książka", "książki"),
    ("gra", "gry"), ("dziewczyna", "dziewczyny"), ("kobieta", "kobiety"), ("noc", "noce"), ("sztuka", "sztuki"),
    ("rzecz", "rzeczy"), ("sprawa", "sprawy"), ("chwila", "chwile"), ("wersja", "wersje"), ("strona", "strony"),
    ("część", "części"), ("linia", "linie"), ("lekcja", "lekcje"), ("odpowiedź", "odpowiedzi"), ("drużyna", "drużyny"),
    ("grupa", "grupy"), ("ekipa", "ekipy"), ("rola", "role"), ("scena", "sceny"), ("kategoria", "kategorie"),
    ("edycja", "edycje"), ("runda", "rundy"), ("seria", "serie"), ("płyta", "płyty"), ("akcja", "akcje"),
    ("zmiana", "zmiany"), ("opcja", "opcje"), ("funkcja", "funkcje"), ("kolejka", "kolejki"), ("bitwa", "bitwy"),
    ("wygrana", "wygrane"), ("przegrana", "przegrane"), ("partia", "partie"), ("mapa", "mapy"), ("postać", "postacie"),
    ("misja", "misje"), ("nazwa", "nazwy"), ("liga", "ligi"), ("klasa", "klasy"), ("rocznica", "rocznice"),
    ("butelka", "butelki"), ("kawa", "kawy"), ("herbata", "herbaty"), ("kanapka", "kanapki"), ("karta", "karty"),
    ("próba", "próby"), ("oferta", "oferty"), ("zasada", "zasady"), ("wpłata", "wpłaty"), ("wypłata", "wypłaty"),
    ("kopia", "kopie"), ("wiosna", "wiosny"), ("sala", "sale"), ("komórka", "komórki"), ("lampa", "lampy"),
    ("sztuczka", "sztuczki"), ("godzinka", "godzinki"), ("minutka", "minutki"), ("sekundka", "sekundki"),
)
_NEUT_SG = frozenset((
    "miejsce", "słowo", "zdanie", "pytanie", "zadanie", "wydarzenie", "święto", "pole", "imię", "jajko", "piwo", "auto",
    "dziecko", "okno", "jabłko", "nagranie", "hasło", "zdjęcie", "wideo", "ciastko", "lato", "życie", "powiadomienie",
    "ogłoszenie", "wejście", "wyjście", "zaproszenie", "ćwiczenie", "spotkanie", "przedstawienie", "wystąpienie",
))
_FEM_SG = frozenset(sg for sg, _pl in _FEM_NOUNS)
_FEM_PL = frozenset(pl for _sg, pl in _FEM_NOUNS)
_RE_NEXT_WORD = re.compile(r"\s+([^\W\d_]+)")


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
_NOUN_POLNOC = {"nom": "północ", "acc": "północ", "gen": "północy", "loc": "północy", "dat": "północy", "instr": "północą"}

# Przypadek wybierany po przyimku. Brak przyimka albo nieznany przyimek: mianownik (= biernik rzeczowników nieżywotnych).
_PREP_CASE_DATE = {
    "w": "loc", "we": "loc", "po": "loc", "przy": "loc",
    "przed": "instr", "nad": "instr", "pod": "instr",
    "do": "gen", "od": "gen", "z": "gen", "ze": "gen", "około": "gen", "dla": "gen", "bez": "gen", "u": "gen", "podczas": "gen",
}
# Dzień miesiąca: domyślnie dopełniacz ("19 listopada" = "dziewiętnastego listopada"), po przyimkach jak wyżej.
_PREP_CASE_DAY = {**_PREP_CASE_DATE, "na": "gen", "między": "instr"}
_PREP_CASE_TIME = {
    "o": "loc", "po": "loc", "w": "loc",
    "do": "gen", "od": "gen", "około": "gen", "z": "gen", "ze": "gen", "dla": "gen",
    "na": "acc", "za": "acc", "przez": "acc", "przed": "instr",
}
# Wieki: po rzeczownikach "początek/koniec/połowa/przełom..." stoi dopełniacz ("na początku XX wieku").
_CENTURY_GOVERNORS = (
    "początku", "początek", "końcu", "koniec", "końca", "połowie", "połowa", "połowy",
    "przełomie", "przełom", "schyłku", "schyłek", "ćwierci", "ćwierć",
)
_PREP_CASE_CENTURY = {**_PREP_CASE_DATE, **{word: "gen" for word in _CENTURY_GOVERNORS}}
_LOCATIVE_PREPS = frozenset({"w", "we", "po", "przy", "o"})


def _case_after(prep: str | None, table: dict[str, str], default: str = "nom") -> str:
    return table.get(prep.strip().lower(), default) if prep else default


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
_NUM_CORE = r"\d{1,3}(?:,\d{3}){2,}(?![\d,])|\d{1,3}(?:\.\d{3}){2,}(?:,\d+)?|\d{1,3}(?:\.\d{3})+,\d+|\d{1,3}(?: \d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?"
_NUM_HEAD = rf"(?P<neg>(?<!\w)-)?(?<![\w.])(?P<num>{_NUM_CORE})"
# Liczba stojąca sama: nie może kończyć się w połowie ułamka ani tuż przed literą ("3D", "A4" zostają bez zmian).
_NUM = _NUM_HEAD + r"(?!\w)(?![.,]\d)"
# Liczba przed jednostką, walutą albo znakiem %: prawą krawędź pilnuje sama jednostka, więc "9,99zł" i "1,5l" działają bez spacji.
_NUM_U = _NUM_HEAD + r"(?![.,]\d)"


@dataclass(frozen=True)
class _Num:
    neg: bool
    int_part: str
    frac: str | None


def _parse(token: str, neg: bool) -> _Num:
    t = token
    if re.fullmatch(r"\d{1,3}(?:,\d{3}){2,}", t):
        t = t.replace(",", "")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t) and (t.count(".") >= 2 or "," in t):
        t = t.replace(".", "")
    t = t.replace(" ", "")
    if "," in t:
        ip, fp = t.split(",", 1)
    elif "." in t:
        ip, fp = t.split(".", 1)
    else:
        ip, fp = t, None
    return _Num(neg, ip, fp)


def _say_int(ip: str, gender: str = "m") -> str:
    if (len(ip) > 1 and ip.startswith("0")) or int(ip) > MAX_CARDINAL:
        return spell_digits(ip)
    return cardinal(int(ip), gender)


def _say_frac(fp: str) -> str:
    rest = fp.lstrip("0")
    lead = len(fp) - len(rest)
    if not rest:
        return " ".join(["zero"] * len(fp))
    if len(rest) <= 3:
        return " ".join(["zero"] * lead + [cardinal(int(rest))])
    return spell_digits(fp)


def say_number(p: _Num, gender: str = "m") -> str:
    text = _say_int(p.int_part, gender if p.frac is None else "m")
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


def _agreement_gender(p: _Num, following: str) -> str:
    """Rodzaj liczebnika 1/2 wybrany po następnym słowie (słownik _FEM_NOUNS/_NEUT_SG); w razie wątpliwości męski."""
    if p.frac is not None:
        return "m"
    value = _int_value(p)
    if value is None:
        return "m"
    found = _RE_NEXT_WORD.match(following)
    word = found.group(1).lower() if found else ""
    if value == 1:
        if word in _FEM_SG:
            return "f"
        if word in _NEUT_SG:
            return "n"
    elif value % 10 == 2 and value % 100 != 12 and word in _FEM_PL:
        return "f"
    return "m"


def _starts_sentence(m: re.Match[str]) -> bool:
    """Czy dopasowanie otwiera zdanie (przed nim tylko początek tekstu, znak końca zdania albo przyimek)."""
    before = m.string[: m.start()]
    return re.search(rf"(?:^|[.!?…\n])\s*(?:(?:{_PREP_ALT_DAY})\s+)?$", before, re.IGNORECASE) is not None


def _sentence_dot(m: re.Match[str], *, opener: bool = False, strict: bool = False) -> str:
    """Skrót z kropką mógł kończyć zdanie: oddajemy kropkę, jeśli dalej jest nowe zdanie albo koniec.

    opener: skrót stoi na początku zdania ("W 1410 r. Polacy..."), więc wielka litera po nim to podmiot, nie nowe zdanie.
    strict: kropkę oddajemy tylko na końcu tekstu albo przed nową linią ("3 tys. Polaków" to jedno zdanie).
    """
    tail = m.string[m.end():]
    rest = tail.lstrip()
    if not rest:
        return "."
    if strict:
        return "." if tail.lstrip(" \t").startswith("\n") else ""
    if opener and rest[0].isupper():
        return ""
    return "." if (rest[0].isupper() or rest[0] in "„\"'(") else ""


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
_CURRENCY_GENDER = {"EUR": "n", "€": "n"}  # "jedno euro"
_SUBUNIT = {
    "zł": ("grosz", "grosze", "groszy"), "PLN": ("grosz", "grosze", "groszy"),
    "EUR": ("cent", "centy", "centów"), "€": ("cent", "centy", "centów"),
    "USD": ("cent", "centy", "centów"), "$": ("cent", "centy", "centów"),
    "GBP": ("pens", "pensy", "pensów"), "£": ("pens", "pensy", "pensów"),
}
_SCALE_UNITS = {"tys.": _SCALES[0], "mln": _SCALES[1], "mld": _SCALES[2]}
_UNIT_FORMS = {
    "km²": ("kilometr kwadratowy", "kilometry kwadratowe", "kilometrów kwadratowych", "kilometra kwadratowego"),
    "cm²": ("centymetr kwadratowy", "centymetry kwadratowe", "centymetrów kwadratowych", "centymetra kwadratowego"),
    "m²": ("metr kwadratowy", "metry kwadratowe", "metrów kwadratowych", "metra kwadratowego"),
    "m³": ("metr sześcienny", "metry sześcienne", "metrów sześciennych", "metra sześciennego"),
    "km": ("kilometr", "kilometry", "kilometrów", "kilometra"),
    "cm": ("centymetr", "centymetry", "centymetrów", "centymetra"),
    "mm": ("milimetr", "milimetry", "milimetrów", "milimetra"),
    "kg": ("kilogram", "kilogramy", "kilogramów", "kilograma"),
    "ml": ("mililitr", "mililitry", "mililitrów", "mililitra"),
    "min": ("minuta", "minuty", "minut", "minuty"),
    "godz.": ("godzina", "godziny", "godzin", "godziny"),
    "sek.": ("sekunda", "sekundy", "sekund", "sekundy"),
    "szt.": ("sztuka", "sztuki", "sztuk", "sztuki"),
    "GB": ("gigabajt", "gigabajty", "gigabajtów", "gigabajta"),
    "MB": ("megabajt", "megabajty", "megabajtów", "megabajta"),
    "TB": ("terabajt", "terabajty", "terabajtów", "terabajta"),
    "kB": ("kilobajt", "kilobajty", "kilobajtów", "kilobajta"),
    "kHz": ("kiloherc", "kiloherce", "kiloherców", "kiloherca"),
    "MHz": ("megaherc", "megaherce", "megaherców", "megaherca"),
    "GHz": ("gigaherc", "gigaherce", "gigaherców", "gigaherca"),
    "Hz": ("herc", "herce", "herców", "herca"),
    "m": ("metr", "metry", "metrów", "metra"),
    "g": ("gram", "gramy", "gramów", "grama"),
    "l": ("litr", "litry", "litrów", "litra"),
}
# Zapisy alternatywne sprowadzamy do jednego klucza ("m2" -> "m²").
_UNIT_ALIASES = {"km2": "km²", "cm2": "cm²", "m2": "m²", "m3": "m³", "KB": "kB"}
_UNIT_GENDER = {"min": "f", "godz.": "f", "sek.": "f", "szt.": "f"}
_UNIT_ALT = "km²|cm²|m²|m³|km2|cm2|m2|m3|km|cm|mm|kg|ml|min|godz\\.|sek\\.|szt\\.|GB|MB|TB|kB|KB|kHz|MHz|GHz|Hz|m|g|l"
_PER_SPEED = {"h": "na godzinę", "s": "na sekundę", "100km": "na sto kilometrów"}
_PER_PRICE = {"kg": "za kilogram", "l": "za litr", "szt": "za sztukę", "szt.": "za sztukę", "m": "za metr", "h": "za godzinę", "godz": "za godzinę", "godz.": "za godzinę"}
_DEGREE_FORMS = ("stopień", "stopnie", "stopni", "stopnia")


def say_currency(p: _Num, key: str) -> str:
    one, few, many, gen_sg = _CURRENCY[key]
    gender = _CURRENCY_GENDER.get(key, "m")
    prefix = "minus " if p.neg else ""
    if p.frac is not None and len(p.frac) <= 2 and len(p.int_part) <= 15:
        minor = int(p.frac.ljust(2, "0"))
        major_value = int(p.int_part)
        parts: list[str] = []
        if major_value or not minor:
            parts.append(f"{cardinal(major_value, gender)} {_noun_for(_Num(False, p.int_part, None), (one, few, many, gen_sg))}")
        if minor:
            s_one, s_few, s_many = _SUBUNIT[key]
            parts.append(f"{cardinal(minor)} {plural_form(minor, s_one, s_few, s_many)}")
        return prefix + " ".join(parts)
    return f"{say_number(_Num(p.neg, p.int_part, p.frac), gender)} {_noun_for(p, (one, few, many, gen_sg))}"


# --- kroki normalizacji ------------------------------------------------------------------------------

_MONTH_ALT = "|".join(_MONTHS_GEN)
_PREP_ALT_DATE = "|".join(sorted(_PREP_CASE_DATE, key=len, reverse=True))
_PREP_ALT_DAY = "|".join(sorted(_PREP_CASE_DAY, key=len, reverse=True))
_PREP_ALT_TIME = "|".join(sorted(_PREP_CASE_TIME, key=len, reverse=True))
_PREP_ALT_CENTURY = "|".join(sorted(_PREP_CASE_CENTURY, key=len, reverse=True))
# Po tych słowach liczba 1900-2100 to ilość, nie rok ("do 2000 osób", "w 2000 zł").
_QUANTITY_WORDS = frozenset((
    "zł", "złotych", "złote", "złoty", "pln", "eur", "euro", "usd", "gbp", "dolarów", "dolary", "procent", "procentów",
    "osób", "osoby", "ludzi", "użytkowników", "graczy", "członków", "uczestników", "widzów", "fanów", "słów", "znaków",
    "punktów", "punkty", "pkt", "razy", "raz", "dni", "dzień", "godzin", "godziny", "minut", "minuty", "sekund", "sztuk",
    "sztuki", "szt", "stron", "kilometrów", "metrów", "kg", "km", "m", "cm", "mm", "g", "l", "ml", "min", "godz", "sek",
    "tys", "mln", "mld", "gb", "mb", "tb", "kb", "hz", "khz", "mhz", "ghz", "wyświetleń", "subskrypcji", "głosów",
    "kopii", "egzemplarzy", "lat", "lata", "miesięcy", "miesiące", "tygodni", "tygodnie", "osobach", "osobami", "osobom",
    "ludziach", "ludźmi", "ludziom", "użytkownikami", "graczami",
))
_UNIT_TAIL = r"(?:zł|PLN|EUR|USD|GBP|€|\$|£|%|tys\.|mln|mld|km|kg|cm|mm|ml|min|m|g|l)(?!\w)"

_RE_PHONE_PLUS = re.compile(r"(?<![\w])\+(\d{2})[ -]?(\d{3})[ -]?(\d{3})[ -]?(\d{3})(?!\w)")
_RE_PHONE_TEL = re.compile(r"(?P<pre>\btel\.?\s*:?\s*)(\d{3})[ -]?(\d{3})[ -]?(\d{3})(?!\w)", re.IGNORECASE)
# Krajowy numer komórkowy bez słowa "tel." (600 700 800, 600-700-800): grupy 3-3-3, pierwsza cyfra 4-9, dalej nie waluta ani jednostka.
_RE_PHONE_BARE = re.compile(rf"(?<![\w.,+-])([4-9]\d{{2}})[ -](\d{{3}})[ -](\d{{3}})(?![\w])(?!\s*{_UNIT_TAIL})")
# Długie ciągi cyfr bez separatorów (PESEL, NIP, numer konta, id z Discorda): czytane cyframi po trzy. Okrągłe "1000000000" zostaje liczbą.
_RE_LONG_DIGITS = re.compile(r"(?<![\w.,])(?!\d{1,3}0{7,}(?!\w))\d{10,}(?!\w)(?![.,]\d)")

_RE_DATE_ISO = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DAY})\s+)?(?<![\w./:-])(?P<y>\d{{4}})-(?P<mo>\d{{2}})-(?P<d>\d{{2}})(?![\w-])", re.IGNORECASE
)
_RE_DATE_NUM = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DAY})\s+)?(?<![\w./:-])(?P<d>\d{{1,2}})(?P<sep>[./-])(?P<mo>\d{{1,2}})(?P=sep)(?P<y>\d{{4}})"
    r"(?:(?P<r>\s*(?:r\.|roku)(?!\w))|(?!\w))",
    re.IGNORECASE,
)
_DATE_TEXT_CORE = rf"(?P<d>\d{{1,2}})\.?\s+(?P<mo>{_MONTH_ALT})(?:\s+(?P<y>\d{{4}})(?:(?P<r>\s*(?:r\.|roku)(?!\w))|(?!\w)))?(?!\w)"
_RE_DATE_TEXT = re.compile(rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DAY})\s+)?(?<!\w){_DATE_TEXT_CORE}", re.IGNORECASE)
_RE_DATE_RANGE = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DAY})\s+)?(?<![\w.])(?P<d1>\d{{1,2}})\.?(?:\s+(?P<w>do|oraz|i|a|na)\s+|\s*(?P<dash>[-–])\s*)"
    rf"(?P<d2>\d{{1,2}})\.?\s+(?P<mo>{_MONTH_ALT})(?:\s+(?P<y>\d{{4}})(?:(?P<r>\s*(?:r\.|roku)(?!\w))|(?!\w)))?(?!\w)",
    re.IGNORECASE,
)
_RE_YEAR_R = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_DATE})\s+)?(?<![\w.])(?P<year>\d{{4}})\s*(?P<r>r\.|roku|rokiem|rok)(?!\w)", re.IGNORECASE
)
_RE_YEAR_NOUN = re.compile(
    r"(?P<prep>(?<!\w)(?:w|we|po|przy|o|do|od|z|ze|przed|za)\s+)?(?<!\w)(?P<noun>rok|roku|rokiem)\s+(?P<year>\d{4})(?![\w.,]?\d)", re.IGNORECASE
)
_RE_YEAR_BARE = re.compile(
    r"(?P<prep>(?<!\w)(?:w|we|przy|do|od|po|przed|z|ze)\s+)(?P<year>(?:19|20)\d{2})(?!\w)(?![.,]?\d)(?P<tail>\s+[^\W\d_]+)?", re.IGNORECASE
)
_ROMAN_CORE = r"[IVXLC]{1,6}"
_RE_ROMAN = re.compile(
    rf"(?P<prep>(?<!\w)(?i:{_PREP_ALT_CENTURY})\s+)?(?<![\w])(?P<roman>{_ROMAN_CORE})\s+(?P<noun>wiek(?:u|iem)?|w\.)(?!\w)"
)
_RE_ROMAN_RANGE = re.compile(
    rf"(?P<prep>(?<!\w)(?i:{_PREP_ALT_CENTURY})\s+)?(?<![\w])(?P<r1>{_ROMAN_CORE})(?:\s*(?P<dash>[-–])\s*|\s+(?P<w>i|do|oraz|a)\s+)"
    rf"(?P<r2>{_ROMAN_CORE})\s+(?P<noun>wiek(?:u|iem)?|w\.)(?!\w)"
)
_RE_TIME = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_TIME})\s+)?(?P<g>godz\.\s*)?(?<![\w:.,])(?P<h>2[0-3]|[01]?\d|24(?=[:.]00))(?P<sep>[:.])(?P<m>[0-5]\d)(?!\w)(?![:.]\d)",
    re.IGNORECASE,
)
_RE_GODZ = re.compile(
    rf"(?P<prep>(?<!\w)(?:{_PREP_ALT_TIME})\s+)?(?P<g>godz\.\s*)(?P<h>2[0-4]|[01]?\d)(?![\w:.,]?\d)(?!\s*{_UNIT_TAIL})", re.IGNORECASE
)
_RE_GODZ_RANGE = re.compile(
    r"(?P<prep>(?<!\w)(?:w|od)\s+)?godz\.\s*(?P<h1>2[0-4]|[01]?\d)(?:[:.]00)?(?:\s*[-–]\s*|\s+do\s+)(?P<h2>2[0-4]|[01]?\d)(?:[:.]00)?(?![\w:.,]?\d)", re.IGNORECASE
)
_RE_DOTTED = re.compile(r"(?<![\w.,])\d+(?:\.\d+){2,}(?![\w]|[.,]\d)")
_RE_PERCENT = re.compile(_NUM_U + r"\s*%")
_RE_CUR_SCALE = re.compile(_NUM_U + r"\s*(?P<scale>tys\.|mln|mld)\s*(?P<cur>zł|PLN|EUR|USD|GBP|€|\$|£)(?!\w)")
_RE_SCALE = re.compile(_NUM_U + r"\s*(?P<scale>tys\.|mln|mld)(?!\w)")
_RE_CUR_SUFFIX = re.compile(_NUM_U + r"\s*(?P<cur>zł|PLN|EUR|USD|GBP|€|\$|£)(?:/(?P<per>kg|l|szt\.?|m|godz\.?|h)(?!\w))?(?!\w)")
_RE_CUR_PREFIX = re.compile(rf"(?P<cur>[€$£])\s*{_NUM}")
_RE_DEGREES = re.compile(_NUM_U + r"\s*°\s*C(?!\w)")
_RE_UNIT = re.compile(_NUM_U + rf"\s?(?P<unit>{_UNIT_ALT})(?:/(?P<per>h|s|100\s?km)(?!\w))?(?!\w)")
_RE_NUMBER = re.compile(_NUM)

# Wyrażenia, które zostają bez zmian (adresy, e-maile, wzmianki Discorda): chronimy je znacznikami na czas normalizacji.
_RE_PROTECT = re.compile(
    r"<(?:@[!&]?|#|a?:\w+:)\d{5,}>"
    r"|(?:https?://|www\.)[^\s<>\"“”„]+"
    r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
)
# Znacznik chronionego fragmentu to jeden znak z obszaru prywatnego (U+E100 + numer): bez cyfr, żeby żaden krok go nie ruszył.
_MARK_BASE = 0xE100
_MARK_LAST = 0xF8FF
_RE_MARK = re.compile("[\ue100-\uf8ff]")
_RE_PRIVATE_USE = re.compile("[\ue000-\uf8ff]")

# (wzorzec pierwszej litery i reszty, rozwinięcie, czy skrót często kończy zdanie). Wielka litera na początku jest zachowana.
_ABBREVIATIONS = (
    (re.compile(r"(?<!\w)([Nn])p\."), "na przykład", False),
    (re.compile(r"(?<!\w)([Mm])\.in\."), "między innymi", False),
    (re.compile(r"(?<!\w)([Ii])td\."), "i tak dalej", True),
    (re.compile(r"(?<!\w)([Ii])tp\."), "i tym podobne", True),
    (re.compile(r"(?<!\w)([Tt])zn\."), "to znaczy", False),
    (re.compile(r"(?<!\w)([Tt])j\."), "to jest", False),
    (re.compile(r"(?<!\w)([Ww])g(?!\w)\.?"), "według", False),
)
# "ok." przed liczbą to "około"; sprawdzamy to przed rozwinięciem cyfr.
_RE_OKOLO = re.compile(r"(?<!\w)([Oo])k\.(?=\s*\d)")


def _num_from(m: re.Match[str]) -> _Num:
    return _parse(m.group("num"), bool(m.group("neg")))


def _capital_like(sample: str, text: str) -> str:
    return text[:1].upper() + text[1:] if sample.isupper() else text


def _protect(s: str) -> tuple[str, list[str]]:
    saved: list[str] = []

    def keep(m: re.Match[str]) -> str:
        token = m.group(0)
        core = token.rstrip(".,;:!?)]}»\"'")
        tail = token[len(core):]
        if _MARK_BASE + len(saved) > _MARK_LAST:
            return token  # zbyt wiele chronionych fragmentów: reszta przechodzi przez zwykłą normalizację
        saved.append(core)
        return f"{chr(_MARK_BASE + len(saved) - 1)}{tail}"

    return _RE_PROTECT.sub(keep, s), saved


def _restore(s: str, saved: list[str]) -> str:
    def back(m: re.Match[str]) -> str:
        index = ord(m.group(0)) - _MARK_BASE
        return saved[index] if 0 <= index < len(saved) else ""

    return _RE_MARK.sub(back, s)


def _step_okolo(s: str) -> str:
    return _RE_OKOLO.sub(lambda m: _capital_like(m.group(1), "około"), s)


def _step_phones(s: str) -> str:
    def plus(m: re.Match[str]) -> str:
        groups = ", ".join(spell_digits(m.group(i)) for i in (2, 3, 4))
        return f"plus {cardinal(int(m.group(1)))}, {groups}"

    def tel(m: re.Match[str]) -> str:
        return m.group("pre") + ", ".join(spell_digits(m.group(i)) for i in (2, 3, 4))

    def bare(m: re.Match[str]) -> str:
        return ", ".join(spell_digits(m.group(i)) for i in (1, 2, 3))

    def long_digits(m: re.Match[str]) -> str:
        digits = m.group(0)
        return ", ".join(spell_digits(digits[i : i + 3]) for i in range(0, len(digits), 3))

    s = _RE_PHONE_TEL.sub(tel, _RE_PHONE_PLUS.sub(plus, s))
    return _RE_LONG_DIGITS.sub(long_digits, _RE_PHONE_BARE.sub(bare, s))


def _day_case(prep: str | None) -> str:
    return _case_after(prep, _PREP_CASE_DAY, default="gen")


def _date_phrase(day: int, month: int, year: int | None, case: str = "gen") -> str | None:
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    text = f"{ordinal_phrase(day, case)} {_MONTHS_GEN[month - 1]}"
    if year is not None:
        if not 1000 <= year <= MAX_ORDINAL:
            return None
        text += f" {ordinal_phrase(year, 'gen')} roku"
    return text


def _step_dates(s: str) -> str:
    def finish(m: re.Match[str], phrase: str) -> str:
        prep = m.group("prep") or ""
        r = m.groupdict().get("r")
        dot = _sentence_dot(m, opener=_starts_sentence(m)) if r and r.rstrip().endswith(".") else ""
        return prep + phrase + dot

    def iso(m: re.Match[str]) -> str:
        phrase = _date_phrase(int(m.group("d")), int(m.group("mo")), int(m.group("y")), _day_case(m.group("prep")))
        return m.group(0) if phrase is None else (m.group("prep") or "") + phrase

    def numeric(m: re.Match[str]) -> str:
        phrase = _date_phrase(int(m.group("d")), int(m.group("mo")), int(m.group("y")), _day_case(m.group("prep")))
        return m.group(0) if phrase is None else finish(m, phrase)

    def textual(m: re.Match[str]) -> str:
        month = _MONTH_INDEX.get(m.group("mo").lower())
        if month is None:  # wielkie "İ" albo długie "ſ" pasują do wzorca bez uwzględniania wielkości liter, ale nie są nazwą miesiąca
            return m.group(0)
        year = int(m.group("y")) if m.group("y") else None
        phrase = _date_phrase(int(m.group("d")), month, year, _day_case(m.group("prep")))
        return m.group(0) if phrase is None else finish(m, phrase)

    def ranged(m: re.Match[str]) -> str:
        month = _MONTH_INDEX.get(m.group("mo").lower())
        if month is None:
            return m.group(0)
        case = _day_case(m.group("prep"))
        d1, d2 = int(m.group("d1")), int(m.group("d2"))
        year = int(m.group("y")) if m.group("y") else None
        tail = _date_phrase(d2, month, year, case)
        if tail is None or not 1 <= d1 <= 31 or d1 >= d2:
            return m.group(0)
        word = m.group("w") or "do"
        lead = "" if m.group("prep") or m.group("w") else "od "
        phrase = f"{lead}{ordinal_phrase(d1, case)} {word} {tail}"
        return finish(m, phrase)

    s = _RE_DATE_ISO.sub(iso, s)
    s = _RE_DATE_NUM.sub(numeric, s)
    s = _RE_DATE_RANGE.sub(ranged, s)
    return _RE_DATE_TEXT.sub(textual, s)


def _step_years(s: str) -> str:
    def with_r(m: re.Match[str]) -> str:
        year = int(m.group("year"))
        if not 1000 <= year <= MAX_ORDINAL:
            return m.group(0)
        prep = m.group("prep") or ""
        noun = m.group("r").lower()
        if prep:
            case = _case_after(m.group("prep"), _PREP_CASE_DATE)
        else:  # bez przyimka rządzi forma zapisanego rzeczownika: "2026 roku" to dopełniacz
            case = {"roku": "gen", "rokiem": "instr"}.get(noun, "nom")
        dot = _sentence_dot(m, opener=_starts_sentence(m)) if noun == "r." else ""
        return f"{prep}{ordinal_phrase(year, case)} {_NOUN_ROK[case]}{dot}"

    def after_noun(m: re.Match[str]) -> str:
        year = int(m.group("year"))
        if not 1000 <= year <= MAX_ORDINAL:
            return m.group(0)
        noun = m.group("noun").lower()
        prep = m.group("prep") or ""
        if noun == "roku":
            case = "loc" if prep.strip().lower() in _LOCATIVE_PREPS else "gen"
        else:
            case = {"rok": "nom", "rokiem": "instr"}[noun]
        return f"{prep}{m.group('noun')} {ordinal_phrase(year, case)}"

    def bare(m: re.Match[str]) -> str:
        year = int(m.group("year"))
        prep = m.group("prep").strip().lower()
        tail = (m.group("tail") or "").strip().lower()
        nxt = m.string[m.end("year") : m.end("year") + 1]
        if tail in _QUANTITY_WORDS or nxt in "%€$£°":
            return m.group(0)
        if prep not in _LOCATIVE_PREPS and not tail:  # "do 2000." bywa ilością: bez dalszego słowa nie zgadujemy
            return m.group(0)
        return f"{m.group('prep')}{ordinal_phrase(year, _case_after(m.group('prep'), _PREP_CASE_DATE))}{m.group('tail') or ''}"

    s = _RE_YEAR_R.sub(with_r, s)
    s = _RE_YEAR_NOUN.sub(after_noun, s)
    return _RE_YEAR_BARE.sub(bare, s)


def _step_roman(s: str) -> str:
    def century(n: int, noun: str, prep: str | None, *, last: bool = True) -> tuple[str, str]:
        if noun == "wiek":
            case = "nom"
        elif noun == "wieku":
            case = _case_after(prep, _PREP_CASE_CENTURY)
            case = case if case in ("loc", "gen") else "gen"
        elif noun == "wiekiem":
            case = "instr"
        else:  # skrót "w."
            case = _case_after(prep, _PREP_CASE_CENTURY)
        return ordinal_phrase(n, case), _NOUN_WIEK[case]

    def ranged(m: re.Match[str]) -> str:
        n1, n2 = _roman_to_int(m.group("r1")), _roman_to_int(m.group("r2"))
        if n1 is None or n2 is None or not (1 <= n1 <= 30 and 1 <= n2 <= 30):
            return m.group(0)
        prep = m.group("prep") or ""
        noun = m.group("noun")
        second, word = century(n2, noun, m.group("prep"))
        # Pierwszy człon dostaje ten sam przypadek co drugi: "XVIII-XIX w." -> "osiemnastego do dziewiętnastego wieku".
        case = _case_after(m.group("prep"), _PREP_CASE_CENTURY)
        case = {"wieku": case if case in ("loc", "gen") else "gen", "wiekiem": "instr", "wiek": "nom"}.get(noun, case)
        first = ordinal_phrase(n1, case)
        loc = prep.strip().lower() in _LOCATIVE_PREPS
        sep = m.group("w") or ("i" if loc else "do")
        lead = "" if (m.group("prep") or m.group("w")) else "od "
        dot = _sentence_dot(m, opener=_starts_sentence(m)) if noun == "w." else ""
        return f"{prep}{lead}{first} {sep} {second} {word}{dot}"

    def single(m: re.Match[str]) -> str:
        n = _roman_to_int(m.group("roman"))
        if n is None or not 1 <= n <= 30:
            return m.group(0)
        prep = m.group("prep") or ""
        noun = m.group("noun")
        spoken, word = century(n, noun, m.group("prep"))
        dot = _sentence_dot(m, opener=_starts_sentence(m)) if noun == "w." else ""
        return f"{prep}{spoken} {word}{dot}"

    return _RE_ROMAN.sub(single, _RE_ROMAN_RANGE.sub(ranged, s))


def _step_times(s: str) -> str:
    def say_time(prep_text: str | None, godz: str | None, hour: int, minute: int) -> str:
        prep = prep_text or ""
        case = _case_after(prep_text, _PREP_CASE_TIME)
        prefix = prep
        if godz:
            noun_case = "loc" if prep.strip().lower() == "o" else case
            prefix += _NOUN_GODZINA[noun_case] + " "
        if hour in (0, 24) and minute == 0 and not godz:
            return prefix + _NOUN_POLNOC[case]
        if hour == 0:
            hour_words = "zero"
        else:
            hour_words = ordinal_phrase(hour, case, "f")
        if minute == 0:
            minutes = ""
        elif minute < 10:
            minutes = f" zero {_UNITS[minute]}"
        else:
            minutes = " " + cardinal(minute)
        return prefix + hour_words + minutes

    def sub(m: re.Match[str]) -> str:
        if m.group("sep") == ".":
            # Kropka jako separator godzin tylko po "godz." albo po przyimku czasu i nie przed walutą czy jednostką ("19.30 zł").
            prep = (m.group("prep") or "").strip().lower()
            minutes = int(m.group("m"))
            plausible = bool(m.group("g")) or prep == "o" or (bool(prep) and (minutes == 0 or minutes > 12))  # "od 1.03" to data, "od 19.00" i "o 8.05" to godziny
            if not plausible or re.match(rf"\s*{_UNIT_TAIL}", m.string[m.end():]):
                return m.group(0)
        return say_time(m.group("prep"), m.group("g"), int(m.group("h")), int(m.group("m")))

    def godz_only(m: re.Match[str]) -> str:
        hour = int(m.group("h"))
        if not 1 <= hour <= 24:
            return m.group(0)
        prep = m.group("prep") or ""
        case = _case_after(m.group("prep"), _PREP_CASE_TIME)
        noun_case = "loc" if prep.strip().lower() == "o" else case
        return f"{prep}{_NOUN_GODZINA[noun_case]} {ordinal_phrase(hour, case, 'f')}"

    def godz_range(m: re.Match[str]) -> str:
        h1, h2 = int(m.group("h1")), int(m.group("h2"))
        if not (1 <= h1 <= 24 and 1 <= h2 <= 24) or h1 >= h2:
            return m.group(0)
        first, second = ordinal_phrase(h1, "gen", "f"), ordinal_phrase(h2, "gen", "f")
        prep = (m.group("prep") or "").strip().lower()
        if prep == "w":
            return f"{m.group('prep')}godzinach od {first} do {second}"
        return f"{m.group('prep') or 'od '}godziny {first} do {second}"

    return _RE_GODZ.sub(godz_only, _RE_TIME.sub(sub, _RE_GODZ_RANGE.sub(godz_range, s)))


def _step_dotted(s: str) -> str:
    """Numery wersji, adresy IP, numeracja punktów ("2.0.3", "pkt 2.1.3"): grupy czytane po kolei, łączone słowem "kropka"."""

    def sub(m: re.Match[str]) -> str:
        token = m.group(0)
        if re.fullmatch(r"\d{1,3}(?:\.\d{3}){2,}", token):
            return token  # 1.234.567 to liczba z kropkami jako separatorami tysięcy: zajmie się nią krok liczb
        return " kropka ".join(_say_int(group) for group in token.split("."))

    return _RE_DOTTED.sub(sub, s)


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
        dot = _sentence_dot(m, strict=True) if m.group("scale").endswith(".") else ""
        return scale_text(_num_from(m), m.group("scale")) + dot

    def cur_suffix(m: re.Match[str]) -> str:
        text = say_currency(_num_from(m), m.group("cur"))
        per = m.group("per")
        return f"{text} {_PER_PRICE[per.lower()]}" if per else text

    def unit(m: re.Match[str]) -> str:
        p = _num_from(m)
        raw = m.group("unit")
        key = _UNIT_ALIASES.get(raw, raw)
        text = f"{say_number(p, _UNIT_GENDER.get(key, 'm'))} {_noun_for(p, _UNIT_FORMS[key])}"
        per = m.group("per")
        if per:
            text += f" {_PER_SPEED[per.replace(' ', '')]}"
        return text + (_sentence_dot(m, strict=True) if key.endswith(".") else "")

    def free(m: re.Match[str]) -> str:
        p = _num_from(m)
        return say_number(p, _agreement_gender(p, m.string[m.end():]))

    s = _RE_CUR_SCALE.sub(cur_scale, s)
    s = _RE_SCALE.sub(only_scale, s)
    s = _RE_CUR_SUFFIX.sub(cur_suffix, s)
    s = _RE_CUR_PREFIX.sub(lambda m: say_currency(_num_from(m), m.group("cur")), s)
    s = _RE_DEGREES.sub(lambda m: f"{say_number(_num_from(m))} {_noun_for(_num_from(m), _DEGREE_FORMS)} Celsjusza", s)
    s = _RE_UNIT.sub(unit, s)
    return _RE_NUMBER.sub(free, s)


def _step_abbreviations(s: str) -> str:
    for pattern, replacement, can_end_sentence in _ABBREVIATIONS:

        def sub(m: re.Match[str], replacement: str = replacement, can_end: bool = can_end_sentence) -> str:
            text = _capital_like(m.group(1), replacement)
            tail = m.string[m.end() : m.end() + 1]
            glued = " " if tail and not tail.isspace() and tail.isalnum() else ""  # "np.kot" -> "na przykład kot"
            return text + (_sentence_dot(m) if can_end else "") + glued

        s = pattern.sub(sub, s)
    return s


def _step_symbols(s: str) -> str:
    s = re.sub(r"\s*&\s*", " i ", s)
    s = re.sub(r"\+", " plus ", s)
    return re.sub(r"\s*=\s*", " równa się ", s)


_DASHES_BEFORE_DIGIT = re.compile(r"(?<![\w)\]])[‐‑‒–—](?=\d)")


def normalize_pl(text: str) -> str:
    """Rozwija liczby, daty, godziny, waluty i częste skróty na słowa gotowe do wypowiedzenia."""
    s = _RE_PRIVATE_USE.sub(" ", text)
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ").replace("−", "-")
    s = _DASHES_BEFORE_DIGIT.sub("-", s)  # "–5°C" z edytora tekstu to liczba ujemna, nie myślnik
    s, saved = _protect(s)
    s = _step_okolo(s)
    for step in (_step_phones, _step_dates, _step_years, _step_roman, _step_times, _step_dotted, _step_numbers, _step_abbreviations, _step_symbols):
        s = step(s)
    s = _restore(s, saved)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in s.split("\n")]
    return "\n".join(lines).strip()


def normalize_for_speech(text: str, language: str) -> str:
    """Normalizacja zależna od języka. Dla innych języków niż polski tekst zostaje bez zmian."""
    return normalize_pl(text) if language.lower().split("-")[0] == "pl" else text
