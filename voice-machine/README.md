# Maszyna Głosów: lokalny silnik

Lokalny serwer MCP, który uczy się głosu Twojego znajomego z jego nagrania i potem mówi nim po polsku (i w 29 innych językach).
Interfejsem jest artefakt „Maszyna Głosów” na Twoim koncie Claude. Model działa u Ciebie na komputerze,
a artefakt woła go przez narzędzia serwera `sakura-voice`.

## Dlaczego tak, a nie w samej stronie

Artefakt to strona w piaskownicy: nie ma sieci, nie może pobrać wag modelu i nie ma na nie miejsca (limit wersji to 256 MB,
a model to kilka GB). Dlatego „uczenie się głosu” dzieje się na Twoim komputerze. Strona łączy się z silnikiem przez mechanizm
`host:` (lokalny serwer MCP) i **działa to tylko w aplikacji Claude na komputerze, dla właściciela artefaktu**. W innym widoku
strona pokaże instrukcję podłączenia, a cztery gotowe głosy Claude będą dostępne tylko tam, gdzie platforma je udostępnia
(zwykle Chrome lub Edge po zalogowaniu; w Firefoksie, Safari i w oknach aplikacji ich nie będzie). Znajomego nie sklonujesz bez silnika.

## Dlaczego VoxCPM2

Wybór opiera się na dowodach zebranych 2026-11-19, z ich ograniczeniami:

| Co | Stan |
|---|---|
| Licencja | Apache-2.0 dla kodu i wag wg README modelu (swobodne użycie komercyjne). XTTS-v2 ma wagi tylko niekomercyjne (CPML). |
| Polski | Na liście 30 języków. Dwie liczbowe tabele dla polskiego, obie od autorów modelu: zestaw MiniMax (100 zdań) daje WER 1,14 i podobieństwo mówcy 88,4 (najwyższe lub blisko najwyższego; ElevenLabs Multilingual v2 ma tam lepszy WER 0,77, ale podobieństwo 72,9, OmniVoice 0,87 / 87,7), a wewnętrzny test autorów (500 zdań) daje WER 1,90% wobec 1,65% u Fish S2-Pro. |
| Jakość dźwięku | Wyjście 48 kHz. Polski tester opisał 24 kHz z OmniVoice jako „stłumione” przy VoxCPM2. |
| Czego NIE wiadomo | Brak niezależnego testu odsłuchowego polskiego dla VoxCPM2. Tabele mierzą rozpoznawanie przez ASR i podobieństwo, nie akcent ani naturalność, a liczby podają sami autorzy. **Posłuchaj sam i porównaj na prawdziwym nagraniu znajomego.** |
| Znane wady | Zgłoszenia użytkowników: ucięte końcówki słów i sporadyczne dodane słowo (ok. 1% zdań w jednym pomiarze). Autorzy radzą wygenerować 1 do 3 razy. |
| Usługi w chmurze | Jedyny znaleziony niezależny test odsłuchowy polskiego (NASK, COLING 2025, słuchacze w Polsce) wygrał ElevenLabs Multilingual v2, a XTTS-v2 wypadł najgorzej. To płatna usługa, która wymaga wysłania próbek głosu znajomego do dostawcy; nie ma dla niej testu klonowania po polsku. Ta aplikacja jest lokalna i takiego silnika nie ma, choć interfejs silnika pozwala go dodać. |

## Wymagania

- Windows 11, aplikacja Claude na komputer, konto z dostępem do artefaktów.
- Python **3.10 do 3.12** (README modelu: `<3.13`; zalecam 3.11). Python 3.13 nie zadziała.
- Karta NVIDIA z CUDA ≥ 12. Autorzy podają ok. 8 GB pamięci karty, użytkownik zgłosił działanie na 6 GB. Na samym procesorze (`-CpuOnly`) model działa, ale bardzo wolno.
- Kilka GB na dysku na model i internet przy pierwszym uruchomieniu (pobranie z Hugging Face). Potem model startuje bez internetu.

## Instalacja (Windows)

W PowerShellu, w folderze `voice-machine`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -TorchIndexUrl <adres z pytorch.org>
```

Pełny zapis jest potrzebny, bo świeży Windows blokuje skrypty `.ps1` (samo `.\scripts\setup-windows.ps1` kończy się błędem „running scripts is disabled on this system”).
`-ExecutionPolicy Bypass` działa tylko dla tego jednego uruchomienia, niczego nie zmienia w systemie i omija też oznaczenie „z internetu” po pobraniu repozytorium jako ZIP.
Na komputerze służbowym polityka firmy może to zablokować: zrób wtedy instalację „Ręcznie” (niżej), która nie uruchamia plików `.ps1`.

Adres PyTorch zależy od Twojej karty i sterownika, więc nie zgaduję go za Ciebie:
wejdź na https://pytorch.org/get-started/locally/, wybierz Stable, Windows, Pip, Python i swoją wersję CUDA, a z wygenerowanego polecenia
weź adres po `--index-url`. Bez karty NVIDIA użyj `-CpuOnly` zamiast `-TorchIndexUrl`.

Skrypt: znajdzie Pythona 3.10-3.12, utworzy `.venv`, zainstaluje PyTorch, sprawdzi, czy PyTorch widzi kartę NVIDIA (jeśli wybrałeś wersję CUDA, a karty nie widać,
zatrzyma się z wyjaśnieniem zamiast po cichu zostawić wolny procesor), zainstaluje `voxcpm==2.0.3` i uruchomi `doctor --load`:
pobierze model, zrobi próbną syntezę (`doctor-smoke.wav`) i próbę klonowania z tego nagrania (`doctor-smoke-clone.wav`; sprawdza to, czy tor klonowania działa
na Twoim komputerze, a nie jakość klonu). Na końcu zapisze `claude-desktop-snippet.json` z Twoimi ścieżkami.
**Posłuchaj `doctor-smoke.wav`** zanim pójdziesz dalej: to jedyny sposób, żeby ocenić, czy głos brzmi sensownie.
Dane (głosy znajomych i nagrania) trafiają do `%USERPROFILE%\SakuraVoiceMachine`.

Ręcznie (to samo bez skryptu):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install torch torchaudio --index-url <adres z pytorch.org>
.\.venv\Scripts\python -m pip install -e ".[voxcpm]"
.\.venv\Scripts\python -m voice_machine doctor --load
```

## Podłączenie do aplikacji Claude

Najprościej (po udanej instalacji), w tym samym folderze:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-windows.ps1 -ConfigOnly -InstallToClaudeConfig
```

Skrypt zrobi kopię zapasową pliku konfiguracji aplikacji Claude i dopisze wpis `sakura-voice` (Twoje własne zmienne `env` w istniejącym wpisie zostają).
Szuka pliku w `%APPDATA%\Claude`, a dla wersji ze sklepu Microsoft w katalogu pakietu; wypisuje, który plik zmienił. Sprawdź w aplikacji
(Ustawienia, Developer, Edit Config), że to ten sam plik.

Ręcznie: w aplikacji Claude (komputerowej) otwórz Ustawienia, Developer, Edit Config. Wpis ma kształt z `claude_desktop_config.example.json`
(przy instalacji ręcznej podstaw własną ścieżkę do `.venv\Scripts\python.exe` i własną nazwę użytkownika w `SVM_DATA_DIR`):

- jeśli plik nie ma klucza `mcpServers`, dopisz cały zapis z `claude-desktop-snippet.json` (albo z przykładu) obok innych kluczy;
- jeśli już ma, skopiuj do niego tylko wpis `"sakura-voice": { ... }`.

Nazwa musi zostać dokładnie `sakura-voice`: z niej strona składa adres `host:sakura-voice`.
Potem zamknij aplikację Claude całkiem (także z zasobnika), uruchom ją ponownie i otwórz artefakt w niej.
Chip „Silnik lokalny” w nagłówku strony powinien zmienić się na „gotowy”. Przy pierwszym wywołaniu aplikacja zapyta o zgodę.

Aplikacja Claude uruchamia serwer z krótką listą zmiennych środowiskowych. Instalator kopiuje do wpisu te, które mają znaczenie
(`HF_HOME`, `HF_HUB_CACHE`, `HF_ENDPOINT`, `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`), jeśli masz je ustawione; przy instalacji ręcznej dopisz je sam w bloku `env`.

Pierwsze ładowanie modelu trwa. Strona pokazuje „ładuje model…”, a przy błędzie wypisuje powód u góry.

## Jak dodać głos znajomego

Przycisk **„+ Dodaj głos znajomego”** jest pod listą „Znajomi”. Wymagania wobec nagrania zależą od modelu i strona bierze je z silnika:

- **Jedno nagranie** (VoxCPM2 używa jednego). Rozsądnie 6 do 15 s czystej mowy jednej osoby, bez muzyki i szumu, w spokojnym, wyraźnym tempie.
  Zakres jest orientacyjny: autorzy nie podają zalecanej długości, a pomiary użytkowników pokazują, że sama długość prawie nie przewiduje jakości,
  za to szybkie tempo mowy pogarsza wynik. Jeśli głos brzmi słabo, spróbuj innego fragmentu nagrania: ten sam człowiek potrafi wypaść bardzo różnie.
- **Transkrypcja** (opcjonalna, ale polecana): dokładny tekst nagrania. Z nią model używa trybu „Ultimate Cloning”, który autorzy zalecają
  dla największego podobieństwa. Dla nagrań po polsku liczby i skróty w transkrypcji rozwijam na słowa; w innych językach wpisz je słowami.
- **Nie odszumiaj agresywnie** nagrania: zgłaszano przekłamania po odszumianiu. Silnik ma odszumianie wyłączone.
- **Zgoda**: formularz wymaga zaznaczenia, że osoba wie o użyciu jej głosu i się zgodziła. Potwierdzenie ląduje w `voice.json` głosu.
- Zapis głosu działa tylko z podłączonym silnikiem. Nagranie możesz wybrać i sprawdzić jego jakość wcześniej, ale po podłączeniu silnika (to wymaga ponownego uruchomienia
  aplikacji Claude) dodajesz je od nowa.
- Przeglądarka sama dekoduje plik (WAV, MP3, M4A, OGG) i wysyła do silnika czysty WAV mono 16 kHz.
- „Anuluj” w trakcie wysyłania naprawdę przerywa zapis: nic nie zostaje zapisane.

Na liście jest też głos „Domyślny (losowy głos modelu)”: to synteza bez nagrania wzorcowego (VoxCPM2 nie ma głosów wbudowanych), więc głos zmienia się
z każdym nagraniem, a czasem nawet między zdaniami. Służy do sprawdzenia, że wszystko działa, nie do pracy.

Głosy trzymane są na dysku: `%USERPROFILE%\SakuraVoiceMachine\voices\` przy instalacji skryptem (zmiana: `SVM_DATA_DIR` albo `--data-dir`;
bez skryptu domyślnie `%LOCALAPPDATA%\SakuraVoiceMachine`). Nagrania znajomych nie trafiają do repozytorium (jest `.gitignore`) i nie opuszczają komputera.
Ruch sieciowy silnika to pobranie modelu z Hugging Face przy pierwszym uruchomieniu; kolejne starty korzystają z kopii na dysku i nie łączą się z internetem
(jeśli kopia jest niekompletna, silnik dociąga brakujące pliki). Po nieudanym ładowaniu (np. zerwane pobieranie) odśwież stronę: silnik próbuje ponownie najwcześniej 30 s po błędzie.

Gdy aplikacja Claude jest pakietem MSIX (wersja ze sklepu Microsoft), Windows przekierowuje nowe pliki serwera w `AppData` do ukrytego folderu pakietu: Eksplorator nie pokaże plików pod ścieżką z „Na dysku”, a odinstalowanie aplikacji usunie głosy. Skrypt wpisuje `SVM_DATA_DIR` poza `AppData`; przy instalacji ręcznej zrób to sam (przykład w `claude_desktop_config.example.json`).

## Jak działa polski tekst

Zanim tekst trafi do modelu, silnik zamienia na słowa to, co modele czytają źle (w praktykach polskich użytkowników to najsłabszy punkt):
liczby i ułamki, procenty, kwoty z odmianą rzeczownika (`1 zł`, `2 zł`, `5 zł`, `12,50 zł`, także sklejone: `9,99zł`), skróty `tys.`/`mln`/`mld`,
jednostki (`5km`, `100 km/h`, `5 m²`, `2,5 GB`), rodzaj liczebników 1 i 2 przy częstych rzeczownikach (`dwie osoby`, `jedna minuta`, `jedno euro`),
daty z zakresami (`19.11.2026`, `19 listopada 2026 r.`, `od 3 do 5 marca`), lata i wieki z przypadkiem wybranym po przyimku
(`w 2026 r.`, `w roku 2026`, `do XIX w.`, `na początku XX w.`), godziny (`o 14:30`, `godz. 19.30`, `godz. 9-17`, `00:00` jako północ),
numery telefonów i długie ciągi cyfr czytane cyframi, numery wersji i adresy IP (`2.0.3`: „dwa kropka zero kropka trzy”)
i kilka częstych skrótów (`np.`, `m.in.`, `itd.`, także z wielkiej litery).
Adresy URL, e-maile i wzmianki z Discorda zostają bez zmian. Wszystko inne też zostaje bez zmian zamiast zgadywania.
Pod polem tekstu strona pokazuje „Jak to zostanie przeczytane”, więc widzisz wynik i możesz coś poprawić.
Podział na fragmenty nie rozcina nazw i adresów po skrótach (`ul. Długa`, `prof. Kowalski`, `św. Jana`).
Znane ograniczenia: liczba przy rzeczowniku w przypadku zależnym („z pięcioma osobami”) jest czytana w mianowniku;
rodzaj 1 i 2 wybiera mały słownik częstych rzeczowników, a nieznany rzeczownik dostaje rodzaj męski;
porządkowe zapisane jako `1.` czytane są jak liczebnik główny z kropką.
Wyłączenie: opcja „Rozwiń liczby, daty, godziny i skróty” w Zaawansowanych (dla głosów Claude ta opcja i podgląd są ukryte, bo czytają tekst bez rozwijania).

## Pliki i regeneracja

Każde nagranie zapisuje się też jako prawdziwy plik WAV w `outputs\` w katalogu danych (to najprostszy sposób,
żeby wrzucić je do Discorda: strona w artefakcie nie może pobierać plików WAV, więc przycisk „Zapisz” daje ZIP z WAV).
Zostaje 300 najnowszych kopii; starsze są usuwane automatycznie (zmiana: `SVM_MAX_OUTPUTS`, `0` wyłącza limit). Pliki o innych nazwach w tym folderze nie są ruszane.
**Usunięcie głosu usuwa jego próbki, ale nie kopie nagrań, które nim wygenerowano**: jeśli ktoś prosi o wycofanie głosu, usuń też pasujące pliki z `outputs\`.
Jeśli wynik ma ucięte słowo albo dodane słowo, wygeneruj jeszcze raz (inne ziarno) albo ustaw to samo ziarno w Zaawansowanych dla powtarzalności.

## Dostrajanie (zmienne środowiskowe w bloku `env` konfiguracji)

| Zmienna | Znaczenie | Domyślnie |
|---|---|---|
| `SVM_ENGINE` | silnik: `voxcpm` albo `fake` (tony do testów) | `voxcpm` |
| `SVM_DEVICE` | `cuda`, `cuda:0`, `cpu` | automatycznie |
| `SVM_DATA_DIR` | katalog na głosy i nagrania | `%LOCALAPPDATA%\SakuraVoiceMachine` (instalator wpisuje `%USERPROFILE%\SakuraVoiceMachine`) |
| `SVM_SAVE_OUTPUTS` | `0` wyłącza kopie WAV na dysku | `1` |
| `SVM_MAX_OUTPUTS` | ile najnowszych kopii WAV zostaje (`0` = bez limitu) | `300` |
| `SVM_PRELOAD` | `0`: nie ładuj modelu przy starcie aplikacji Claude, tylko przy otwarciu strony | `1` |
| `SVM_VOXCPM_MODEL` | identyfikator modelu albo lokalny katalog | `openbmb/VoxCPM2` |
| `SVM_VOXCPM_TIMESTEPS` | liczba kroków (jakość kontra szybkość; niekalibrowane) | `10` |
| `SVM_VOXCPM_CFG` | siła prowadzenia (`cfg_value`) | `2.0` |
| `SVM_VOXCPM_CHUNK_CHARS` | najdłuższy fragment tekstu na jedno wywołanie (niekalibrowane) | `240` |
| `SVM_VOXCPM_OPTIMIZE` | `1` włącza `torch.compile` (bywa kłopotliwe na Windows) | wyłączone |

Silnik ładuje model od razu po starcie aplikacji Claude i trzyma go w pamięci karty, dopóki aplikacja działa. Jeśli wolisz zwalniać kartę,
ustaw `SVM_PRELOAD=0`: model załaduje się dopiero, gdy otworzysz stronę. Całkowicie offline możesz też wymusić `HF_HUB_OFFLINE=1`.

## Co zostało sprawdzone, a czego nie

| Element | Stan |
|---|---|
| Serwer MCP, kolejka zadań, magazyn głosów, walidacja WAV, normalizacja polskiego tekstu | Testy automatyczne w środowisku, w którym powstał kod (pytest, silnik testowy zamiast modelu). |
| Protokół MCP po stdio, w tym odporność na śmieci na stdout | Test z prawdziwym klientem MCP SDK 2.3.0 i podprocesem serwera. |
| Strona: dodawanie głosu, anulowanie, odtwarzanie, ZIP, stany błędów, układ mobilny | Playwright (Chromium) z atrapą środowiska `window.claude` zgodną z typami kontraktu i z prawdziwym serwerem MCP przez most HTTP. |
| Adapter VoxCPM2 | Testy na atrapach o prawdziwych sygnaturach plus testy, które porównują użyte argumenty, atrybuty i stałe ze źródłami `voxcpm` 2.0.3 (patrz „Testy”). Sprawdziłem, że łapią zmianę nazwy argumentu, atrybutu i wersji. |
| **Prawdziwy model VoxCPM2** | **NIE uruchamiany.** W środowisku, w którym powstał kod, nie było wag ani dostępu do Hugging Face. Jakość głosu i działanie na Twojej karcie potwierdza dopiero `doctor --load`. |
| **Most `host:` w aplikacji Claude** | **NIE sprawdzany.** Strona woła narzędzia przez kontrakt z typów, ale nie było tu aplikacji, która by je przekazała. Możliwe, że aplikacja będzie prosić o potwierdzenie każdego wywołania, które nie jest tylko odczytem. Nie wiadomo też, czy host ogranicza rozmiar wyniku narzędzia (kawałki audio mają ok. 600 tys. znaków base64). |
| **`scripts/setup-windows.ps1`** | **NIE uruchamiany** (brak PowerShella). Jest krótki, każdy krok wypisuje, co robi, a testy sprawdzają to, co da się sprawdzić bez niego (BOM, domknięcie tekstów, polecenia z `-ExecutionPolicy`). |
| Zgodność serwera (SDK MCP 2.x) z Twoją wersją aplikacji Claude | Niesprawdzona. |
| Reguły polskiego tekstu | Sprawdzone testami i na ponad tysiącu przykładów w automatycznym przeglądzie (oceniał je model językowy, nie człowiek), ale nie na słuch: to, czy model wymawia wynik dobrze, wychodzi dopiero w odsłuchu. |

## Rozwiązywanie problemów

| Objaw | Co zrobić |
|---|---|
| „running scripts is disabled on this system” | Uruchom skrypt zapisem z `-ExecutionPolicy Bypass` (sekcja „Instalacja”). |
| „Silnik lokalny: niepodłączony” | Otwórz artefakt w aplikacji Claude na komputerze (nie w przeglądarce). Sprawdź, że wpis nazywa się `sakura-voice` i że uruchomiłeś aplikację ponownie. Przycisk „Sprawdź ponownie” w karcie instrukcji sprawdza połączenie bez przeładowania strony. |
| „brak zgody” | W menu Uprawnienia artefaktu zezwól na serwer lokalny. |
| `doctor` pisze o Pythonie | Potrzebny Python 3.10-3.12. Zainstaluj 3.11 i utwórz nowe `.venv`. |
| Chip „błąd ładowania” | Powód jest u góry strony i w logach serwera MCP aplikacji Claude (stderr). Po przyczynie łączności odśwież stronę (silnik próbuje ponownie najwcześniej 30 s po błędzie). |
| `[UWAGA] karta CUDA: niedostępna` | PyTorch bez CUDA albo brak karty NVIDIA: model działa na procesorze, bardzo wolno. Z kartą zainstaluj PyTorch z adresem z pytorch.org dla swojej wersji CUDA. |
| Błąd `WinError 126` albo `1114` przy PyTorch | Zainstaluj „Visual C++ Redistributable x64” (https://aka.ms/vs/17/release/vc_redist.x64.exe). `WinError 1455`: zwiększ plik wymiany Windows. |
| „Za mało pamięci karty graficznej” | Skróć tekst, zamknij inne programy korzystające z karty; model potrzebuje ok. 8 GB (zgłoszono działanie na 6 GB). |
| Wpis w konfiguracji Claude nie działa | Wersja aplikacji ze sklepu Microsoft może czytać inny plik niż `%APPDATA%\Claude`. Użyj Ustawienia, Developer, Edit Config, żeby zobaczyć właściwy. |
| „Na dysku: …” na stronie, a pliku nie ma w Eksploratorze | Pakiet MSIX przekierował `AppData`: szukaj w `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Local\SakuraVoiceMachine\`, a na stałe ustaw `SVM_DATA_DIR` poza `AppData`. |

## Testy

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
```

Pięć testów kontraktowych (zgodność adaptera ze źródłami `voxcpm` 2.0.3: nazwy argumentów, atrybuty, wersja) uruchamia się samo, gdy w środowisku jest zainstalowany `voxcpm`
(tak jest po instalacji z tego README). Gdzie indziej są pomijane, chyba że ustawisz `SVM_VOXCPM_SOURCE_DIR` na katalog z rozpakowanym wheel `voxcpm` 2.0.3.
Pozostałe testy nie zależą od tego, czy w środowisku jest PyTorch albo `voxcpm`.

Test strony w przeglądarce (wymaga Node z Playwrightem i Chromium):

```powershell
$env:PYTHON = ".\.venv\Scripts\python.exe"
node e2e/run_e2e.cjs
```

## Narzędzia MCP serwera `sakura-voice`

`status`, `list_voices`, `preview_text` (tylko odczyt), `voice_upload_begin`, `voice_upload_chunk`, `voice_upload_commit`, `voice_upload_abort`,
`delete_voice`, `speak`, `job_status`, `job_audio`, `job_cancel`. Tekst błędu zawiera kod w nawiasach kwadratowych, np. `[E_NOT_READY] opis`
(klient MCP dopisuje przed nim `Error executing tool ...`). Wejście narzędzia w artefakcie jest ograniczone do 1 MiB, dlatego próbki idą w kawałkach po ok. 600 kB,
a audio w kawałkach po ok. 450 kB (base64 jest wtedy tylko w `structuredContent`, nie dwa razy).

## Licencje i odpowiedzialność

Kod w tym folderze to część repozytorium strony. VoxCPM2: Apache-2.0 wg README modelu. Autorzy modelu zastrzegają, że klonowania
nie wolno używać do podszywania się, oszustw ani dezinformacji, i zalecają oznaczanie treści generowanych przez AI. Dodawaj tylko głosy osób,
które się na to zgodziły.
