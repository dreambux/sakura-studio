# Pet: Eklipsa (Sekret)

Pet w stylu Pet Simulator X / 99: **ciało to jeden sześcian** (lekko zaokrąglone krawędzie) z twarzą na przedniej ścianie,
małe kostki-łapki pod spodem, pet unosi się nad ziemią. Dodatki (skrzydła, rogi, kryształy, wstęgi) mają swobodne kształty.
Sześcian jest rozdarty świecącym piorunem na dwie połówki.
- **Lód (lewa):** jasny błękit, pierzaste skrzydło z płomienistych piór, kryształy, jasne spirale, białe kły.
- **Pustka (prawa):** ciemny fiolet, skrzydło nietoperza z pazurami, rogi, kolce na karku, oko w świecących pierścieniach, fioletowe kły.
- Świecący szew-piorun przez środek głowy, rozdarta aureola nad głową, kryształy z pierścieniami na orbicie.

Pliki w `export/`:
- `Eklipsa.glb`: model (≈25 tys. trójkątów w 4 częściach, każda < 18 tys.; `Paleta`, `Paleta1`, `Neon`, `NeonLod`), przodem w -Z
- `Eklipsa_paleta.png`: tekstura-paleta z gradientami (jedna na cały model)
- `Eklipsa_hero.png`, `Eklipsa_widoki.png`: rendery
- `Eklipsa.blend`: scena Blendera

## Do Roblox Studio
1. Zaimportuj `Eklipsa.glb` (3D Importer). Tekstura palety wczyta się sama.
2. Części `Neon` i `NeonLod` ustaw na Material = Neon (kolor fioletowy / jasnoniebieski). Pozostałe: SmoothPlastic.
3. Sześcian ma 4 study, z dodatkami model ma ok. 15 studów szerokości. Do peta w świecie: `Model:ScaleTo(0.4)`.
4. Unoszenie i obrót (bobbing) zrób skryptem peta (np. sinus na wysokości).

Przebudowa: `python pets/build_pet.py` (moduł `bpy`).

# Pet: Mruczek (Rzadki)

Kot-sześcian: rudy pręgowany, słodkie oczy kawaii (wielka błyszcząca źrenica, zielony półksiężyc tęczówki, duży i mały błysk, gwiazdka, rzęsy), biały pyszczek i pierś, różowy nosek, uszy z różowym środkiem,
pręgi na czole, grzbiecie i bokach, puszysty ogon z kremowym końcem, cztery krótkie łapki z białymi skarpetkami.
Jeden materiał (paleta), ok. 19,8 tys. trójkątów w 2 częściach.

Pliki: `export/Mruczek.glb`, `Mruczek_paleta.png`, `Mruczek_hero.png`, `Mruczek_widoki.png`, `Mruczek.blend`.
Przebudowa: `python pets/build_cat.py`. W Robloxie: zaimportuj GLB, materiał SmoothPlastic, `Model:ScaleTo(0.45)`.
