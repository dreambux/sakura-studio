# Szamka

Demonstracyjny serwis do zamawiania jedzenia z dostawą: lista lokali, menu, koszyk, kasa, śledzenie zamówienia na mapie i panel admina, w którym da się zmienić lokale, menu, ceny i zamówienia.

To statyczna strona (HTML, CSS, JS) bez serwera. Nie ma tu prawdziwych płatności ani prawdziwych zamówień, a stopka mówi o tym wprost. Marka i ilustracje są własne.

## Panel admina

- Wejście: adres strony z `#/admin` na końcu albo pięć szybkich kliknięć w „© 2026 Szamka” w stopce.
- PIN startowy to `1234`. Zmienisz go w zakładce Ustawienia. PIN chroni tylko przed przypadkowym wejściem, bo strona nie ma serwera.
- Po wejściu na każdej stronie sklepu widać w rogu ciemny pasek ze skrótami. Kłódka na pasku blokuje panel i chowa pasek.

W panelu są cztery zakładki:

| Zakładka | Co zmienisz |
| --- | --- |
| Zamówienia | Nowe zamówienie z dowolnego lokalu, pozycje, kwoty, odbiorca, adres, kurier, godzina, etap i okno z napisem, że to żart. Stąd skopiujesz też link do śledzenia. |
| Lokale | Nazwa, opis, okładka, logo, kolor, oceny, czas i koszt dostawy, promocje, kolejność na liście oraz całe menu z wariantami i dodatkami. |
| Ustawienia | Teksty na stronie głównej, kuchnie, kody rabatowe, opłata serwisowa, imiona kurierów, domyślne dane w kasie, PIN. |
| Dane | Kopia zapasowa, wczytanie kopii, plik `dane.js` dla wszystkich odwiedzających, powrót do danych startowych. |

## Gdzie są dane

Zmiany z panelu, zamówienia i koszyk zapisują się w `localStorage` przeglądarki, osobno na każdym urządzeniu. Kto wejdzie na stronę z innego urządzenia, zobaczy dane startowe z pliku `js/dane.js`.

- Żeby zmiany w lokalach i menu zobaczył każdy: w zakładce Dane pobierz nowy `dane.js` i podmień nim `js/dane.js`.
- Żeby pokazać komuś konkretne zamówienie: wyślij link do śledzenia. Całe zamówienie jest zapisane w samym linku, więc działa na każdym urządzeniu.

## Pliki

| Plik | Zawartość |
| --- | --- |
| `index.html` | Szkielet strony. |
| `styles.css` | Wygląd sklepu i panelu. |
| `js/ilustracje.js` | Rysowane w SVG talerze, okładki lokali, stół na stronie głównej i mapa dostawy. |
| `js/dane.js` | Dane startowe: lokale, menu, ustawienia. |
| `js/app.js` | Sklep: lista lokali, menu, koszyk, kasa, śledzenie, historia. |
| `js/admin.js` | Panel admina. |

Stronę można otworzyć prosto z dysku (`index.html`) albo wrzucić cały folder na dowolny hosting plików.
