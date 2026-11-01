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
| `koncepty/` | 14 konceptów map: widok z góry z opisem (`_gora.png`), z boku (`_bok.png`), układ (`_uklad.lua/.json`), teren (`_teren.glb`) |
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
