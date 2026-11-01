# Ostatni Legion: mapy, tekstury i dekoracje

Wszystko powstaje w Blenderze (skrypty Python, tryb tła), w **jednym stylu**: ręcznie malowane
pociągnięcia pędzla na bazie szumu, ten sam filtr kolorów, cienkie pęknięcia i drobne wgłębienia.
Gęstość jest wszędzie taka sama: 128 px na stud.

## Zawartość

| Folder | Co jest w środku |
|---|---|
| `textures/` | ~170 bezszwowych tekstur: `<nazwa>_col.png` (kolor) i `<nazwa>_nrm.png` (normal map) |
| `katalog_tekstur/` | plansze podglądu tekstur per kategoria (Ścieżki, Podłoża, Trawy, Skały, Ściany, Rośliny, Materiały) |
| `modele/<Kategoria>.glb` | modele dekoracji do Roblox Studio (każdy model jako osobny obiekt, nazwa = nazwa z katalogu) |
| `modele/katalog.json` | spis modeli: kategoria, opis, plik, liczba trójkątów, punkty efektów (ogień, światło, dym) |
| `modele/dekoracje.blend` | wszystkie modele w jednym pliku Blendera |
| `katalog/<Kategoria>.png` | miniatury wszystkich modeli |
| `koncepty/` | 15 konceptów map: widok z góry z opisem (`_gora.png`), z boku (`_bok.png`), układ (`_uklad.lua/.json`), teren (`_teren.glb`) |
| `lib/` | kod: `tex.py` + `recipes.py` + `library.py` (tekstury), `props.py` + `p_*.py` (modele), `mapscene.py` + `m_maps*.py` (koncepty) |

## Budowanie

```bash
python maps/build_textures.py          # tekstury + plansze (python z modułem bpy albo blender -b -P)
python maps/build_props.py             # modele + GLB + katalog miniatur
python maps/build_maps.py              # 14 konceptów (render z góry i z boku, układ Luau)
```

## Do Roblox Studio

1. **Modele:** zaimportuj `modele/<Kategoria>.glb` (3D Importer) i wrzuć modele do `ServerStorage.MapAssets`.
   Punkty efektów z `katalog.json` (Fire, Light, Smoke, Sparkles, Mist, Portal, Water, Embers) zamień na
   instancje Fire/PointLight/ParticleEmitter.
2. **Tekstury podłoża i ścieżek:** wgraj `_col.png` i `_nrm.png` jako MaterialVariant (Studio → Material Manager)
   i maluj nimi teren albo party. Skala: 1 kafel = 8 studów (podłoża i ścieżki) albo 4 study (modele).
3. **Mapa z konceptu:** `roblox/MapBuilder.lua` stawia wszystkie dekoracje i waypointy z pliku `koncepty/<nr>_<Mapa>_uklad.lua`.
   Teren i ścieżki odtwórz według renderu z góry (widać na nim skalę 20 studów).
4. **Klimat („shadery”):** `roblox/MapLighting.lua`, czyli preset Lighting, Atmosphere, Bloom, ColorCorrection,
   SunRays, DepthOfField i Clouds, kolor wody i żar w powietrzu dla każdej mapy.

## 14 map: różne układy i poziomy trudności

| Nr | Mapa | Poziom | Układ ścieżek | Klimat |
|---|---|---|---|---|
| 01 | Zatoka Pireusu | ŁATWY | 1 bardzo długa serpentyna | port w słońcu, morze dookoła, flota |
| 02 | Agora Ateńska | ŁATWY | 1 długa pętla przez miasto | marmurowe miasto, Partenon na wzgórzu |
| 03 | Ogrody Hesperyd | ŁATWY | 1 kręta ścieżka z kamieni w trawie | bujny ogród o zachodzie, stawy |
| 04 | Labirynt Knossos | ŚREDNI | 2 wejścia łączą się na dziedzińcu | pałac minojski, złota godzina |
| 05 | Wyrocznia Delficka | ŚREDNI | serpentyny po tarasach | zbocze z tarasami, tholos |
| 06 | Stadion Olimpii | ŚREDNI | 2 okrążenia bieżni wokół środka | stadion, trybuny, ołtarz Zeusa |
| 07 | Wyspa Kirke | ŚREDNI | 2 kładki nad bagnem łączą się na wyspie | magiczny zmierzch, archipelag |
| 08 | Termopile | TRUDNY | 2 ścieżki szybko w jeden wąwóz | wąski pas między klifem a morzem |
| 09 | Mury Troi | TRUDNY | 2 równoległe szturmy pod bramę | oblężenie, koń trojański |
| 10 | Zbocza Olimpu | TRUDNY | 2 krótkie, osobne ścieżki | szczyt nad chmurami, rzeka |
| 11 | Zatopiona Atlantyda | TRUDNY | 3 groble do środka | laguna z ruinami pod wodą |
| 12 | Lodowe Wrota Boreasza | TRUDNY | 2 spirale | śnieg, lód, zamarznięta rzeka |
| 13 | Bramy Hadesu | KOSZMAR | 3 krótkie ścieżki przez Styks | podziemia, zielone ognie duchów |
| 14 | Kuźnia Hefajstosa | KOSZMAR | 3 krótkie ścieżki zbiegające się przy bazie | wulkan nocą, lawa |
| 15 | Brama Lwów | ŚREDNI | 1 wąż: miasto, most nad rzeką, gimnazjon | miasto z Olintu, rzeka, akropol, 14 platform skalnych |


## Nowe: modele w wysokiej jakości i platformy pod jednostki

`lib/p_hq.py` podmienia słabsze modele (te same nazwy, więc mapy działają bez zmian). Organiczne bryły
(zwierzęta, posągi) są rzeźbione z szkieletu modyfikatorami Skin i Subdivision (`lib/sculpt.py`), a nie składane z pudełek.
Wzorowane na zabytkach:

- **Posągi ludzi:** postać o heroicznych proporcjach (7,5 głowy), z pozami: hoplita z hełmem korynckim, aspis i dory;
  Atena w peplosie z hełmem zsuniętym na czoło; zwycięzca z wieńcem; dyskobol; Kora z polichromią; Apollo z lirą;
  Nike z Samotraki na dziobie okrętu; popiersie filozofa; herma. `statue_fig` w starych modelach też używa nowej postaci.
- **Zwierzęta:** lew siedzący (typ z Amfipolis i Cheronei) z grzywą z loków; Sfinks Naksyjczyków na wczesnej kolumnie
  jońskiej z wolutami; koń z brązu z uniesioną nogą; Pegaz ze skrzydłami z warstw piór; byk minojski; orzeł Zeusa;
  **Cerber**: trzy psie głowy z otwartymi paszczami, kłami, uszami i kolczastymi obrożami, z ogonem-wężem.
- **Domy (typ z Olintu, V–IV w. p.n.e.):** kamienny cokół i ściany z cegły mułowej z tynkiem wapiennym; dziedziniec z bruku z
  pastas (portyk na drewnianych słupach), cysterną, ołtarzem i amforami; dachy z płaskich dachówek z rzędami imbreksów
  (każdy imbreks osobno) i antefiksami; końce belek pod okapem; drewniane drzwi z ćwiekami i małe okna z okiennicami.
  Do tego dom piętrowy z loggią, wiejski dom z pergolą winorośli i dom wyspiarski z Akrotiri (płaski dach, kamienne narożniki,
  okna w ramach z belek) zamiast nowożytnego domu z niebieską kopułą.
- **Broń:** dory z liściastym grotem i sauroterem, xiphos z liściastą głownią, aspis z wypukłą czaszą, brązowym rantem i godłem
  (lambda, gwiazda, maczuga, trójząb), hełm koryncki (otwory oczu, nosal, policzki, grzebień). Z tych części są stojak
  z bronią, stos tarcz, tropaion i pobojowisko.
- **Unikaty:** skrzynia skarbów z ~460 pojedynczymi monetami, klejnotami, perłami i pucharem; puszka Pandory na lwich łapach
  z dwuspadowym wiekiem i fioletową mgłą; hełm Hadesa z ogniem dusz; koń trojański z desek na kołach.

`lib/p_platforms.py`: **Platformy** (19 modeli). Są to duże skały z płaskim wierzchem, na których stają jednostki:
fasetowany klif, gruba warstwa wierzchu (ziemia, trawa, piasek, marmurowy bruk, popiół, śnieg), głazy u podstawy, kępki
trawy, kamienne schody, ruiny, wersja dwupoziomowa i wysoka iglica dla snajperów. Każda ma marker `Stand`
(środek, wysokość i promień pola do stawiania) w `katalog.json`, więc skrypt gry wie, gdzie wolno postawić jednostkę.
