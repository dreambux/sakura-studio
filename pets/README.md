# Pet: Eklipsa (Sekret)

Kanciasty (blokowy) pet w stylu pet simulatora: leżąca smocza głowa rozdarta na dwie połówki.
- **Lód (lewa):** jasny błękit, pierzaste skrzydło z płomienistych piór, kryształy, jasne spirale, białe kły.
- **Pustka (prawa):** ciemny fiolet, skrzydło nietoperza z pazurami, rogi, kolce na karku, oko w świecących pierścieniach, fioletowe kły.
- Świecący szew-piorun przez środek głowy, rozdarta aureola nad głową, kryształy z pierścieniami na orbicie.

Pliki w `export/`:
- `Eklipsa.glb`: model (≈5,3 tys. trójkątów; części: `Paleta`, `Neon`, `NeonLod`), przodem w -Z
- `Eklipsa_paleta.png`: tekstura-paleta z gradientami (jedna na cały model)
- `Eklipsa_hero.png`, `Eklipsa_widoki.png`: rendery
- `Eklipsa.blend`: scena Blendera

## Do Roblox Studio
1. Zaimportuj `Eklipsa.glb` (3D Importer). Tekstura palety wczyta się sama.
2. Części `Neon` i `NeonLod` ustaw na Material = Neon (kolor fioletowy / jasnoniebieski). Pozostałe: SmoothPlastic.
3. Model ma ok. 13 studów długości. Do peta w świecie: `Model:ScaleTo(0.3)` (ok. 4 study), w podglądzie jajka może być większy.
4. Unoszenie i obrót (bobbing) zrób skryptem peta (np. sinus na wysokości).

Przebudowa: `python pets/build_pet.py` (moduł `bpy`).
