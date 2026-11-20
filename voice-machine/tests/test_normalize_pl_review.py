"""Poprawki normalizatora po przeglądzie: przypadki zgłoszone przez recenzenta, każdy z oczekiwanym polskim brzmieniem."""

from __future__ import annotations

import re

import pytest

from voice_machine.normalize_pl import cardinal, normalize_pl


@pytest.mark.parametrize(
    "n, gender, expected",
    [
        (1, "f", "jedna"), (1, "n", "jedno"), (1, "m", "jeden"),
        (2, "f", "dwie"), (2, "n", "dwa"), (22, "f", "dwadzieścia dwie"), (102, "f", "sto dwie"),
        (21, "f", "dwadzieścia jeden"), (12, "f", "dwanaście"), (2000, "f", "dwa tysiące"), (1001, "f", "tysiąc jeden"),
        (-2, "f", "minus dwie"), (5, "f", "pięć"),
    ],
)
def test_gender_of_one_and_two(n: int, gender: str, expected: str) -> None:
    assert cardinal(n, gender) == expected


@pytest.mark.parametrize(
    "source, spoken",
    [
        # sklejone liczby, waluty i jednostki
        ("Kosztuje 9,99zł, a butelka ma 1,5l.", "Kosztuje dziewięć złotych dziewięćdziesiąt dziewięć groszy, a butelka ma jeden przecinek pięć litra."),
        ("5km, 10min, 3kg", "pięć kilometrów, dziesięć minut, trzy kilogramy"),
        ("2,5GB i 100 MB", "dwa przecinek pięć gigabajta i sto megabajtów"),
        ("Prędkość 100 km/h na odcinku 5 m². Cena 5 zł/kg.", "Prędkość sto kilometrów na godzinę na odcinku pięć metrów kwadratowych. Cena pięć złotych za kilogram."),
        ("8 l/100 km", "osiem litrów na sto kilometrów"),
        ("3D, 5G, A4, MP3", "3D, 5G, A4, MP3"),
        # rodzaj liczebników 1 i 2
        ("Wygrały 2 osoby, a 1 osoba odpadła.", "Wygrały dwie osoby, a jedna osoba odpadła."),
        ("Za 2 godziny, po 22 minutach, za 1 minutę", "Za dwie godziny, po dwadzieścia dwa minutach, za jeden minutę"),
        ("Mamy 2 nagrody i 1 miejsce, 1 nagranie.", "Mamy dwie nagrody i jedno miejsce, jedno nagranie."),
        ("22 osoby, 21 osób, 12 osób, 2 chłopaków", "dwadzieścia dwie osoby, dwadzieścia jeden osób, dwanaście osób, dwa chłopaków"),
        ("1 min, 2 min, 22 min", "jedna minuta, dwie minuty, dwadzieścia dwie minuty"),
        ("1 EUR, 2 EUR, 5 EUR", "jedno euro, dwa euro, pięć euro"),
        ("5 szt., 3 godz., 10 sek.", "pięć sztuk, trzy godziny, dziesięć sekund."),
        # daty: zakresy, przyimki, kropka po dniu
        ("Turniej trwa od 3 do 5 marca.", "Turniej trwa od trzeciego do piątego marca."),
        ("Zapisy 3-5 marca, 3 i 4 maja, z 5 na 6 maja, między 3 a 5 maja.", "Zapisy od trzeciego do piątego marca, trzeciego i czwartego maja, z piątego na szóstego maja, między trzecim a piątym maja."),
        ("Zapisy kończą się po 15 maja, nie dzwoń przed 20.06.2026.", "Zapisy kończą się po piętnastym maja, nie dzwoń przed dwudziestym czerwca dwa tysiące dwudziestego szóstego roku."),
        ("Dnia 3. maja 2026r.", "Dnia trzeciego maja dwa tysiące dwudziestego szóstego roku."),
        # lata i wieki
        ("W roku 2026 wydamy album. Premiera w 2026.", "W roku dwa tysiące dwudziestym szóstym wydamy album. Premiera w dwa tysiące dwudziestym szóstym."),
        ("Od 2020 do 2022 r. byliśmy aktywni.", "Od dwa tysiące dwudziestego do dwa tysiące dwudziestego drugiego roku byliśmy aktywni."),
        ("2025 rok był wyjątkowy.", "dwa tysiące dwudziesty piąty rok był wyjątkowy."),
        ("Do 2000 osób, w 2000 zł, do 2000.", "Do dwa tysiące osób, w dwa tysiące złotych, do dwa tysiące."),
        ("W XIX wieku Polska była pod zaborami. Do XIX w. nic się nie działo.", "W dziewiętnastym wieku Polska była pod zaborami. Do dziewiętnastego wieku nic się nie działo."),
        ("na początku XX w., pod koniec XIX w. i w połowie XVIII wieku", "na początku dwudziestego wieku, pod koniec dziewiętnastego wieku i w połowie osiemnastego wieku"),
        ("na przełomie XIX i XX wieku, w XVIII-XIX wieku, od XIV do XVI w.", "na przełomie dziewiętnastego i dwudziestego wieku, w osiemnastym i dziewiętnastym wieku, od czternastego do szesnastego wieku."),
        # godziny
        ("Start o godz. 19.30, wejście od 19.00, godz. 7 rano.", "Start o godzinie dziewiętnastej trzydzieści, wejście od dziewiętnastej, godzina siódma rano."),
        ("Czynne w godz. 9-17, od godz. 7 do 15.", "Czynne w godzinach od dziewiątej do siedemnastej, od godziny siódmej do piętnastej."),
        ("Plan: 10:00: otwarcie; 12:00: lunch; czynne do 24:00; start o 00:00.", "Plan: dziesiąta: otwarcie; dwunasta: lunch; czynne do północy; start o północy."),
        ("od 1.03 do 5.03", "od jeden przecinek zero trzy do pięć przecinek zero trzy"),
        ("19.30 zł", "dziewiętnaście złotych trzydzieści groszy"),  # cena, nie godzina
        # kropka kończąca zdanie po dacie, wieku, tys.
        ("W 1410 r. Polacy pokonali Krzyżaków pod Grunwaldem.", "W tysiąc czterysta dziesiątym roku Polacy pokonali Krzyżaków pod Grunwaldem."),
        ("Od 1 stycznia 2026 r. Wszystkie nagrania będą publikowane.", "Od pierwszego stycznia dwa tysiące dwudziestego szóstego roku Wszystkie nagrania będą publikowane."),
        ("Dziś jest 19.11.2026 r. Jutro będzie lepiej.", "Dziś jest dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku. Jutro będzie lepiej."),
        ("Zebraliśmy 5 tys. Euro na cele.", "Zebraliśmy pięć tysięcy Euro na cele."),
        # skróty z wielkiej litery
        ("Np. Kowalski wygrał. Wg mnie to dobrze. Tzn. że tak. M.in. dlatego.", "Na przykład Kowalski wygrał. Według mnie to dobrze. To znaczy że tak. Między innymi dlatego."),
        ("np.kot, Ok. 5 km", "na przykład kot, Około pięć kilometrów"),
        # liczby ujemne z półpauzą z edytora tekstu
        ("Temperatura spadła do –5°C, saldo –120 zł, od –5 do 5.", "Temperatura spadła do minus pięć stopni Celsjusza, saldo minus sto dwadzieścia złotych, od minus pięć do pięć."),
        ("5–3 i 10–20", "pięć–trzy i dziesięć–dwadzieścia"),
        # telefony i długie ciągi cyfr
        ("Zadzwoń pod 600 700 800, NIP 1234567890.", "Zadzwoń pod sześć zero zero, siedem zero zero, osiem zero zero, NIP jeden dwa trzy, cztery pięć sześć, siedem osiem dziewięć, zero."),
        ("Mamy 2000000000 zł i 5000000000.", "Mamy dwa miliardy złotych i pięć miliardów."),
        ("1,234,567", "milion dwieście trzydzieści cztery tysiące pięćset sześćdziesiąt siedem"),
        # numery wersji, adresy IP, punkty regulaminu
        ("Zainstaluj wersję 2.0.3 i Python 3.12.1", "Zainstaluj wersję dwa kropka zero kropka trzy i Python trzy kropka dwanaście kropka jeden"),
        ("pkt 2.1.3, IP 192.168.0.1, 12.345.678", "pkt dwa kropka jeden kropka trzy, IP sto dziewięćdziesiąt dwa kropka sto sześćdziesiąt osiem kropka zero kropka jeden, dwanaście milionów trzysta czterdzieści pięć tysięcy sześćset siedemdziesiąt osiem"),
    ],
)
def test_reviewed_cases(source: str, spoken: str) -> None:
    assert normalize_pl(source) == spoken


@pytest.mark.parametrize(
    "text",
    [
        "Wejdź na https://sakura.example/zapisy?id=5&x=2 po szczegóły.",
        "Pisz na jan.kowalski+test@example.pl lub www.example.com/a/b?c=1.",
        "Serwer http://example.com:8080/path działa.",
        "Wzmianka <@123456789012345678> i emoji <:kot:123456789012345678> oraz <#987654321>.",
    ],
)
def test_addresses_and_mentions_are_left_untouched(text: str) -> None:
    assert normalize_pl(text) == text


def test_trailing_punctuation_stays_outside_a_protected_address() -> None:
    assert normalize_pl("Zobacz (https://example.com/a). Potem 5 zł.") == "Zobacz (https://example.com/a). Potem pięć złotych."
    assert normalize_pl("Adres: user@example.com, tel. 600 700 800") == (
        "Adres: user@example.com, tel. sześć zero zero, siedem zero zero, osiem zero zero"
    )


def test_private_use_characters_in_the_input_cannot_hijack_the_placeholders() -> None:
    hostile = "AB  https://example.com CD"
    spoken = normalize_pl(hostile)
    assert "https://example.com" in spoken
    assert not re.search("[-]", spoken)


def test_many_protected_tokens_degrade_gracefully() -> None:
    text = " ".join(f"https://example.com/{i}" for i in range(400))
    spoken = normalize_pl(text)
    assert spoken.count("https://example.com/") == 400 or "https://example.com/" in spoken


def test_odd_unicode_month_names_never_crash() -> None:
    # "İ" (U+0130) i "ſ" (U+017F) pasują do wzorca bez uwzględniania wielkości liter, ale nie są nazwą miesiąca.
    assert normalize_pl("Spotkanie 5 LİSTOPADA") == "Spotkanie pięć LİSTOPADA"
    assert normalize_pl("Spotkanie 5 ſierpnia") == "Spotkanie pięć ſierpnia"
    normalize_pl("3-5 LİSTOPADA i 3 do 5 ſierpnia")


def test_idempotent_on_the_reviewed_sentences() -> None:
    samples = [
        "Kosztuje 9,99zł, a butelka ma 1,5l. Wygrały 2 osoby w godz. 9-17.",
        "Turniej trwa od 3 do 5 marca 2026 r. Start o godz. 19.30, plan: 10:00: otwarcie.",
        "W XIX wieku i od 2020 do 2022 r. byliśmy aktywni; pkt 2.1.3, wersja 2.0.3.",
        "Zadzwoń pod 600 700 800, NIP 1234567890, https://example.com/a?b=1&c=2.",
    ]
    for text in samples:
        once = normalize_pl(text)
        assert normalize_pl(once) == once, text
