# Maszyna Głosów: lokalny silnik

Lokalny serwer MCP, który uczy się głosu Twojego znajomego z jego nagrania i potem mówi nim po polsku (i w 29 innych językach).
Interfejsem jest artefakt „Maszyna Głosów” na Twoim koncie Claude. Model działa u Ciebie na komputerze,
a artefakt woła go przez narzędzia serwera `sakura-voice`.

## Dlaczego tak, a nie w samej stronie

Artefakt to strona w piaskownicy: nie ma sieci, nie może pobrać wag modelu i nie ma na nie miejsca (limit wersji to 256 MB,
a model to kilka GB). Dlatego „uczenie się głosu” dzieje się na Twoim komputerze. Strona łączy się z silnikiem przez mechanizm
`host:` (lokalny serwer MCP) i **działa to tylko w aplikacji Claude na komputerze, dla właściciela artefaktu**. W zwykłej
przeglądarce strona pokaże instrukcję podłączenia i nadal da Ci cztery gotowe głosy Claude, ale nie sklonuje znajomego.

## Dlaczego VoxCPM2

Wybór opiera się na dowodach zebranych 2026-11-19, z ich ograniczeniami:

| Co | Stan |
|---|---|
| Licencja | Apache-2.0 dla kodu i wag wg README modelu (swobodne użycie komercyjne). XTTS-v2 ma wagi tylko niekomercyjne (CPML). |
| Polski | Na liście 30 języków. W jedynej znalezionej liczbowej tabeli dla polskiego (zestaw MiniMax, 100 zdań) ma WER 1,14 i podobieństwo mówcy 88,4, czyli najlepsze lub wśród najlepszych obok OmniVoice (0,87 / 87,7). |
| Jakość dźwięku | Wyjście 48 kHz. Polski tester opisał 24 kHz z OmniVoice jako „stłumione” przy VoxCPM2. |
| Czego NIE wiadomo | Brak niezależnego testu odsłuchowego polskiego. Tabela mierzy rozpoznawanie przez ASR i podobieństwo, nie akcent ani naturalność, a liczby podają sami autorzy. **Posłuchaj sam i porównaj na prawdziwym nagraniu znajomego.** |
| Znane wady | Zgłoszenia użytkowników: ucięte końcówki słów i sporadyczne dodane słowo (ok. 1% zdań w jednym pomiarze). Autorzy radzą wygenerować 1 do 3 razy. |

## Wymagania

- Windows 11, aplikacja Claude na komputer, konto z dostępem do artefaktów.
- Python **3.10 do 3.12** (README modelu: `<3.13`; zalecam 3.11). Python 3.13 nie zadziała.
- Karta NVIDIA z CUDA ≥ 12. Autorzy podają ok. 8 GB pamięci karty, użytkownik zgłosił działanie na 6 GB. Na samym procesorze model działa, ale bardzo wolno.
- Kilka GB na dysku na model i internet przy pierwszym uruchomieniu (pobranie z Hugging Face).

## Instalacja (Windows)

W PowerShellu, w folderze `voice-machine`:

```powershell
.\scripts\setup-windows.ps1 -TorchIndexUrl <adres z pytorch.org>
```

Adres PyTorch zależy od Twojej karty i sterownika, więc nie zgaduję go za Ciebie:
wejdź na https://pytorch.org/get-started/locally/, wybierz Stable, Windows, Pip, Python i swoją wersję CUDA, a z wygenerowanego polecenia
weź adres po `--index-url`. Bez karty NVIDIA użyj `-CpuOnly`.

Skrypt: znajdzie Pythona 3.10-3.12, utworzy `.venv`, zainstaluje PyTorch i `voxcpm==2.0.3`, uruchomi `doctor --load`
(pobierze model, zrobi próbną syntezę do `doctor-smoke.wav`) i zapisze `claude-desktop-snippet.json` z Twoimi ścieżkami.
**Posłuchaj `doctor-smoke.wav`** zanim pójdziesz dalej: to jedyny sposób, żeby ocenić, czy głos brzmi sensownie.

Ręcznie (to samo bez skryptu):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install torch torchaudio --index-url <adres z pytorch.org>
.\.venv\Scripts\python -m pip install -e ".[voxcpm]"
.\.venv\Scripts\python -m voice_machine doctor --load
```

## Podłączenie do aplikacji Claude

1. Aplikacja Claude (komputerowa): Ustawienia, Developer, Edit Config. To otwiera właściwy plik konfiguracji.
2. Do sekcji `mcpServers` wklej zawartość `claude-desktop-snippet.json` (kształt w `claude_desktop_config.example.json`).
   Nazwa musi zostać dokładnie `sakura-voice`: z niej strona składa adres `host:sakura-voice`.
   Skrypt z `-InstallToClaudeConfig` dopisze wpis sam i zrobi kopię zapasową.
3. Zamknij aplikację Claude całkiem (także z zasobnika), uruchom ją ponownie i otwórz artefakt w niej.
4. Chip „Silnik lokalny” w nagłówku strony powinien zmienić się na „gotowy”. Przy pierwszym wywołaniu aplikacja zapyta o zgodę.

Pierwsze ładowanie modelu trwa. Strona pokazuje „ładuje model…”, a przy błędzie wypisuje powód u góry.

## Jak dodać głos znajomego

Przycisk **„+ Dodaj głos znajomego”** jest pod listą „Znajomi”. Wymagania wobec nagrania zależą od modelu i strona bierze je z silnika:

- **Jedno nagranie** (VoxCPM2 używa jednego). Rozsądnie 6 do 15 s czystej mowy jednej osoby, bez muzyki i szumu, w spokojnym, wyraźnym tempie.
  Zakres jest orientacyjny: autorzy nie podają zalecanej długości, a pomiary użytkowników pokazują, że sama długość prawie nie przewiduje jakości,
  za to szybkie tempo mowy pogarsza wynik.
- **Transkrypcja** (opcjonalna, ale polecana): dokładny tekst nagrania. Z nią model używa trybu „Ultimate Cloning”, który autorzy zalecają
  dla największego podobieństwa. Liczby i skróty w transkrypcji rozwijam na słowa.
- **Nie odszumiaj agresywnie** nagrania: zgłaszano przekłamania po odszumianiu. Silnik ma odszumianie wyłączone.
- **Zgoda**: formularz wymaga zaznaczenia, że osoba wie o użyciu jej głosu i się zgodziła. Potwierdzenie ląduje w `voice.json` głosu.
- Nagranie możesz przygotować na stronie nawet bez podłączonego silnika. Zapis ruszy po jego podłączeniu.
- Przeglądarka sama dekoduje plik (WAV, MP3, M4A, OGG) i wysyła do silnika czysty WAV mono 16 kHz.

Głosy trzymane są na dysku: `%LOCALAPPDATA%\SakuraVoiceMachine\voices\` (zmiana: `SVM_DATA_DIR` albo `--data-dir`).
Nagrania znajomych nie trafiają do repozytorium (jest `.gitignore`) i nie opuszczają komputera.
Jedyny ruch sieciowy silnika to pobranie modelu z Hugging Face przy pierwszym uruchomieniu.

## Jak działa polski tekst

Zanim tekst trafi do modelu, silnik zamienia na słowa to, co modele czytają źle (w praktykach polskich użytkowników to najsłabszy punkt):
liczby i ułamki, procenty, kwoty z odmianą rzeczownika (`1 zł`, `2 zł`, `5 zł`, `12,50 zł`), skróty `tys.`/`mln`/`mld`,
jednostki, daty (`19.11.2026`, `19 listopada 2026 r.`), lata i wieki z przypadkiem wybranym po przyimku (`w 2026 r.`, `do XIX w.`),
godziny (`o 14:30`) i kilka częstych skrótów (`np.`, `m.in.`, `itd.`). Wszystko inne zostaje bez zmian zamiast zgadywania.
Pod polem tekstu strona pokazuje „Jak to zostanie przeczytane”, więc widzisz wynik i możesz coś poprawić.
Znane ograniczenie: liczba przy rzeczowniku w przypadku zależnym („z pięcioma osobami”) jest czytana w mianowniku.
Wyłączenie: opcja „Rozwiń liczby, daty, godziny i skróty” w Zaawansowanych.

## Pliki i regeneracja

Każde nagranie zapisuje się też jako prawdziwy plik WAV w `%LOCALAPPDATA%\SakuraVoiceMachine\outputs\` (to najprostszy sposób,
żeby wrzucić je do Discorda: strona w artefakcie nie może pobierać plików WAV, więc przycisk „Zapisz” daje ZIP z WAV).
Jeśli wynik ma ucięte słowo albo dodane słowo, wygeneruj jeszcze raz (inne ziarno) albo ustaw to samo ziarno w Zaawansowanych dla powtarzalności.

## Dostrajanie (zmienne środowiskowe w bloku `env` konfiguracji)

| Zmienna | Znaczenie | Domyślnie |
|---|---|---|
| `SVM_ENGINE` | silnik: `voxcpm` albo `fake` (tony do testów) | `voxcpm` |
| `SVM_DEVICE` | `cuda`, `cuda:0`, `cpu` | automatycznie |
| `SVM_DATA_DIR` | katalog na głosy i nagrania | `%LOCALAPPDATA%\SakuraVoiceMachine` |
| `SVM_SAVE_OUTPUTS` | `0` wyłącza kopie WAV na dysku | `1` |
| `SVM_VOXCPM_MODEL` | identyfikator modelu albo lokalny katalog | `openbmb/VoxCPM2` |
| `SVM_VOXCPM_TIMESTEPS` | liczba kroków (jakość kontra szybkość; niekalibrowane) | `10` |
| `SVM_VOXCPM_CFG` | siła prowadzenia (`cfg_value`) | `2.0` |
| `SVM_VOXCPM_CHUNK_CHARS` | najdłuższy fragment tekstu na jedno wywołanie (niekalibrowane) | `240` |
| `SVM_VOXCPM_OPTIMIZE` | `1` włącza `torch.compile` (bywa kłopotliwe na Windows) | wyłączone |

## Co zostało sprawdzone, a czego nie

| Element | Stan |
|---|---|
| Serwer MCP, kolejka zadań, magazyn głosów, walidacja WAV, normalizacja polskiego tekstu | Testy automatyczne w środowisku, w którym powstał kod (pytest, silnik testowy zamiast modelu). |
| Protokół MCP po stdio, w tym odporność na śmieci na stdout | Test z prawdziwym klientem MCP SDK 2.3.0 i podprocesem serwera. |
| Strona: dodawanie głosu, odtwarzanie, ZIP, stany błędów, układ mobilny | Playwright (Chromium) z atrapą środowiska `window.claude` zgodną z typami kontraktu i z prawdziwym serwerem MCP przez most HTTP. |
| Adapter VoxCPM2 | Testy na atrapach o prawdziwych sygnaturach plus test, który porównuje użyte argumenty i stałe ze źródłami `voxcpm` 2.0.3 (`SVM_VOXCPM_SOURCE_DIR`). |
| **Prawdziwy model VoxCPM2** | **NIE uruchamiany.** W środowisku, w którym powstał kod, nie było wag ani dostępu do Hugging Face. Jakość głosu i działanie na Twojej karcie potwierdza dopiero `doctor --load`. |
| **Most `host:` w aplikacji Claude** | **NIE sprawdzany.** Strona woła narzędzia przez kontrakt z typów, ale nie było tu aplikacji, która by je przekazała. Możliwe, że aplikacja będzie prosić o potwierdzenie każdego wywołania, które nie jest tylko odczytem. |
| **`scripts/setup-windows.ps1`** | **NIE uruchamiany** (brak PowerShella). Jest krótki i każdy krok wypisuje, co robi. |
| Zgodność serwera (SDK MCP 2.x) z Twoją wersją aplikacji Claude | Niesprawdzona. |

## Rozwiązywanie problemów

| Objaw | Co zrobić |
|---|---|
| „Silnik lokalny: niepodłączony” | Otwórz artefakt w aplikacji Claude na komputerze (nie w przeglądarce). Sprawdź, że wpis nazywa się `sakura-voice` i że uruchomiłeś aplikację ponownie. |
| „brak zgody” | W menu Uprawnienia artefaktu zezwól na serwer lokalny. |
| `doctor` pisze o Pythonie | Potrzebny Python 3.10-3.12. Zainstaluj 3.11 i utwórz nowe `.venv`. |
| Chip „błąd ładowania” | Powód jest u góry strony i w logach serwera MCP aplikacji Claude (stderr). |
| „bez karty graficznej … bardzo wolna” | PyTorch bez CUDA albo brak karty NVIDIA. Zainstaluj PyTorch z adresem z pytorch.org dla swojej wersji CUDA. |
| Zła wersja Claude ze sklepu Microsoft | Ścieżka konfiguracji może być inna. Użyj Ustawienia, Developer, Edit Config. |

## Testy

```powershell
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
```

Test strony w przeglądarce (wymaga Node z Playwrightem i Chromium):

```powershell
$env:PYTHON = ".\.venv\Scripts\python.exe"
node e2e/run_e2e.cjs
```

## Narzędzia MCP serwera `sakura-voice`

`status`, `list_voices`, `preview_text` (tylko odczyt), `voice_upload_begin`, `voice_upload_chunk`, `voice_upload_commit`, `voice_upload_abort`,
`delete_voice`, `speak`, `job_status`, `job_audio`, `job_cancel`. Błędy mają postać `[KOD] opis`. Wejście narzędzia w artefakcie jest ograniczone do
1 MiB, dlatego próbki i audio idą w kawałkach po ok. 600 kB.

## Licencje i odpowiedzialność

Kod w tym folderze to część repozytorium strony. VoxCPM2: Apache-2.0 wg README modelu. Autorzy modelu zastrzegają, że klonowania
nie wolno używać do podszywania się, oszustw ani dezinformacji, i zalecają oznaczanie treści generowanych przez AI. Dodawaj tylko głosy osób,
które się na to zgodziły.
