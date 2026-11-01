"""Pozostale 10 konceptow (razem 14 map). Kazda mapa ma inny teren, uklad sciezek, klimat i tlo."""
import math

from .mapscene import MapScene
from .m_maps import blob, in_ellipse, piraeus, knossos, olympus, hephaestus


def ring_pts(cx, cy, rx, ry, a0, a1, n=24):
    return [(cx + math.cos(math.radians(a0 + (a1 - a0) * i / n)) * rx,
             cy + math.sin(math.radians(a0 + (a1 - a0) * i / n)) * ry) for i in range(n + 1)]


# ====================================================================== AGORA ATENSKA (latwa)
def agora():
    M = MapScene('AgoraAtenska', 'Agora Atenska', 'LATWY - dluga petla przez miasto', (230, 180))
    M.ground([(-120, 92), (120, 92), (120, -92), (-120, -92)], 'paving_large', z=0, depth=4, cliff_tex='blocks', name='city')
    M.ground([(-60, 40), (60, 40), (60, -30), (-60, -30)], 'paving_marble', z=0.08, depth=1, cliff_tex='blocks', name='agora')
    M.plateau(70, 62, 34, 22, 6.0, 'rocky_ground', 'cliff_white', seed=21, name='acropolis')
    route = [(-112, -78), (-80, -78), (-80, -44), (80, -44), (80, -78), (104, -78), (104, 20), (72, 20), (72, 52)]
    route = [(-112, -78), (-84, -78), (-84, 70), (-30, 70), (-30, 54), (40, 54)]
    route = [(-112, -80), (-86, -80), (-86, 60), (-44, 60), (-44, -50), (6, -50), (6, 30), (36, 30), (36, -60),
             (100, -60), (100, 30), (70, 40)]
    M.path(route, 9, 'cobble_warm', label='Sciezka', color=(255, 90, 60))
    M.place('brama_portal_czerwony', -104, -80, 0, 90, 0.8)
    M.label(-104, -68, 'SPAWN (brama miejska)', (255, 140, 120))
    M.place('swiatynia_dorycka', 72, 64, 6.0, 0, 0.7)
    M.label(72, 88, 'BAZA: Partenon na Akropolu', (140, 220, 255))
    M.place('schody', 70, 38, 0, 0, 1.0)
    M.place('kolumnada_stoa', -18, 22, 0.08, 0, 1.0)
    M.place('kolumnada_stoa', 24, -16, 0.08, 180, 1.0)
    M.place('fontanna_posejdona', -18, -10, 0.08, 0, 0.6)
    for x, y in ((-60, 30), (-60, 10), (-60, -10)):
        M.place('stragan', x + 52, y + 0, 0.08, 90, 0.9) if False else None
    for k in range(5):
        M.place('stragan' if k % 2 else 'stragan_niebieski', 20 + k * 7, 12, 0.08, 180, 0.8)
    M.place('posag_bogini', 54, 6, 0.08, 180, 0.9)
    M.place('popiersie', -28, -22, 0.08, 0, 1.0)
    M.place('herma', 54, -20, 0.08, 0, 1.0)
    for x, y in ((-104, 70), (-60, 82), (-14, 84), (16, 84), (-110, 30), (-112, -10), (-60, -76), (-20, -80), (60, -80),
                 (112, -20), (112, -82), (-20, 84)):
        M.place('dom_grecki_pietrowy' if (x // 10) % 2 else 'dom_grecki', x, y, 0, M.rnd.choice((0, 90, 180, 270)), 0.9)
        M.block(x, y, 9)
    M.scatter(('drzewo_oliwne', 'cyprys', 'krzew_oleander', 'bukszpan_kula', 'lampa_oliwna', 'amfory_grupa',
               'skrzynie_stos', 'lawka', 'kwiaty', 'drzewo_cytrynowe'), 70, (-115, -88, 115, 88), r=3.5)
    M.lighting(sun_rot=(45, 0, 30), sky=(0.52, 0.68, 0.95), sky_e=0.9, sun_e=5.0)
    return M, ['1 dluga sciezka meandrujaca przez miasto - LATWA',
               'Srodek: agora z fontanna Posejdona, dwie stoa, stragany',
               'Baza: Partenon na wzgorzu Akropolu (NE), schody',
               'Brak wody - mapa zamknieta zabudowa miasta']


# ====================================================================== OGRODY HESPERYD (latwa)
def hesperides():
    M = MapScene('OgrodyHesperyd', 'Ogrody Hesperyd', 'LATWY - kreta sciezka przez ogrod', (230, 180))
    M.water(color=(0.05, 0.32, 0.36))
    M.ground(blob(0, 0, 114, 86, seed=31, amp=0.1), 'sand', z=0, depth=6, cliff_tex='rock_warm', name='island')
    M.ground(blob(0, 0, 104, 78, seed=32, amp=0.1), 'grass_meadow', z=0.06, depth=1, cliff_tex='sand', name='garden')
    for cx, cy in ((-40, 30), (44, -36)):
        M.ground(blob(cx, cy, 14, 10, seed=cx), 'water', z=-0.3, depth=0.2, cliff_tex='water', name='pond')
        M.place('lilie_wodne', cx, cy, -0.2, 0, 1.6)
        M.block(cx, cy, 15)
    route = [(-108, 0), (-84, 0), (-74, -30), (-50, -50), (-20, -40), (-10, -10), (-20, 14), (-6, 50), (24, 56), (40, 30),
             (30, 4), (60, -6), (84, 10), (82, 40)]
    M.path(route, 8, 'stepping_grass', label='Sciezka', color=(255, 90, 60), curb='blocks_mossy')
    M.place('luk_teczy', -108, 0, 0, 90, 0.9)
    M.label(-104, 14, 'SPAWN (teczowy luk)', (255, 140, 120))
    M.place('zlota_jablon', 86, 54, 0.06, 0, 1.2)
    M.place('tholos', 86, 54, 0.06, 0, 0.6) if False else None
    M.label(86, 74, 'BAZA: Zlota jablon Hesperyd', (140, 220, 255))
    M.block(86, 54, 12)
    M.place('zlote_runo', 60, 66, 0.06, 0, 0.9)
    for x, y in ((-30, -10), (10, 30), (50, 20), (-60, -20)):
        M.place('fontanna', x, y, 0.06, 0, 0.8)
        M.block(x, y, 5)
    for x in range(-90, 90, 20):
        M.place('bukszpan_stozek', x, -74, 0.06, 0, 0.9)
        M.place('bukszpan_stozek', x, 72, 0.06, 0, 0.9)
    M.scatter(('drzewo_cytrynowe', 'granatowiec', 'drzewo_kwitnace', 'drzewo_figowe', 'krzew_oleander', 'bukszpan_kula',
               'kwiaty', 'lawenda', 'winorosl', 'zywoplot', 'posag_bogini', 'lawka'), 90, (-105, -78, 105, 78), r=4,
              inside=in_ellipse(0, 0, 100, 74))
    M.lighting(sun_rot=(75, 0, -70), sun_col=(1.0, 0.78, 0.55), sun_e=4.2, sky=(0.95, 0.7, 0.55), sky_e=0.8)
    return M, ['1 kreta sciezka z kamieni w trawie - LATWA',
               'Bujny ogrod: drzewa cytrynowe, granaty, kwitnace migdaly, bukszpany',
               'Stawy z liliami, fontanny, zlote runo jako easter egg',
               'Wyspa o zachodzie slonca, morze dookola']


# ====================================================================== WYROCZNIA DELFICKA (srednia)
def delphi():
    M = MapScene('WyroczniaDelficka', 'Wyrocznia Delficka', 'SREDNI - serpentyny w gore tarasow', (230, 180))
    M.ground([(-120, 92), (120, 92), (120, -92), (-120, -92)], 'grass_dry', z=0, depth=6, cliff_tex='cliff', name='slope')
    M.plateau(0, 40, 100, 40, 6.0, 'grass_rocky', 'cliff_white', seed=41, name='terrace1')
    M.plateau(0, 62, 70, 24, 12.0, 'paving_sandstone', 'cliff_white', seed=42, name='terrace2')
    route = [(-112, -80), (100, -80), (100, -56), (-100, -56), (-100, -30), (96, -30), (96, -6), (-60, -6)]
    M.path(route, 8, 'flagstone_dirt', label='Serpentyny (dolny taras)', color=(255, 90, 60))
    M.place('brama_portal_zielony', -104, -80, 0, 90, 0.8)
    M.label(-104, -68, 'SPAWN', (255, 140, 120))
    M.place('tholos', 0, 62, 12.0, 0, 0.8)
    M.label(0, 86, 'BAZA: Swiatynia Apollina (taras gorny)', (140, 220, 255))
    M.place('trojnog_delficki', -40, 40, 6.0, 0, 1.0)
    M.place('omfalos', 40, 40, 6.0, 0, 1.0)
    M.place('skarbczyk', -70, 34, 6.0, 0, 0.9)
    M.place('skarbczyk', 70, 34, 6.0, 0, 0.9)
    M.place('trybuny_stadionu', 0, 20, 6.0, 180, 1.0)
    M.place('sfinks_naksyjski', -30, 10, 6.0, 0, 0.8)
    M.place('lira', 30, 12, 6.0, 0, 1.0)
    M.scatter(('cyprys', 'cyprys_2', 'drzewo_oliwne', 'skaly_grupa', 'glaz_bialy', 'kepa_trawy_sucha', 'krzew_oliwny',
               'stela_nagrobna', 'herma', 'kamyki'), 80, (-115, -88, 115, -2), r=3.5)
    M.scatter(('cyprys', 'krzew_ciemny', 'kwiaty'), 20, (-90, 14, 90, 46), r=4, z=6.0, margin_path=0)
    M.place('gory_tlo', 0, 200, 0, 0, 1.6)
    M.lighting(sun_rot=(40, 0, 150), sun_col=(1.0, 0.93, 0.8), sun_e=4.6, sky=(0.6, 0.7, 0.92))
    return M, ['Sciezka zygzakiem po dolnym tarasie (4 dlugie serpentyny) - SREDNIA',
               'Tarasy na zboczu: trojnog Pytii, omfalos, skarbczyki, sfinks',
               'Baza na gornym tarasie: tholos Apollina',
               'Brak wody, gory w tle, cyprysy']


# ====================================================================== STADION OLIMPII (srednia)
def olympia():
    M = MapScene('StadionOlimpii', 'Stadion Olimpii', 'SREDNI - dwa okrazenia biezni', (230, 180))
    M.ground([(-120, 92), (120, 92), (120, -92), (-120, -92)], 'grass_lush', z=0, depth=4, cliff_tex='cliff', name='land')
    M.ground(ring_pts(0, 0, 92, 50, 0, 360, 48), 'sand_path', z=0.05, depth=1, cliff_tex='sand', name='track')
    M.ground(ring_pts(0, 0, 76, 34, 0, 360, 48), 'grass_short', z=0.08, depth=1, cliff_tex='sand', name='infield')
    lap1 = ring_pts(0, 0, 86, 44, 180, 540, 40)
    lap2 = ring_pts(0, 0, 80, 39, 180, 450, 30)
    route = [(-112, 80), (-86, 40)] + lap1 + lap2 + [(0, -10)]
    M.path(route, 7, 'paving_sandstone', label='Bieznia (2 okrazenia)', color=(255, 90, 60))
    M.place('brama_portal_czerwony', -108, 80, 0, 45, 0.8)
    M.label(-100, 90, 'SPAWN (wejscie zawodnikow)', (255, 140, 120))
    M.place('oltarz', 0, -10, 0.08, 0, 2.0)
    M.label(0, 8, 'BAZA: Oltarz Zeusa (srodek stadionu)', (140, 220, 255))
    for sy in (-1, 1):
        for x in (-60, -30, 0, 30, 60):
            M.place('trybuny_stadionu', x, sy * 66, 0, 0 if sy > 0 else 180, 1.0)
            M.block(x, sy * 66, 9)
    M.place('dyskobol', -40, -10, 0.08, 0, 0.8)
    M.place('posag_wojownika', 40, -10, 0.08, 0, 0.8)
    M.place('kraterowa_waza', -20, 10, 0.08, 0, 1.0)
    M.place('kraterowa_waza', 20, 10, 0.08, 0, 1.0)
    M.place('swiatynia_dorycka', 0, -82, 0, 0, 0.45)
    M.scatter(('drzewo_oliwne', 'drzewo_oliwne_2', 'platan', 'cyprys', 'krzew', 'lawka', 'namiot_wojskowy', 'sztandar',
               'kosz_owocow', 'stojak_broni'), 60, (-118, -90, 118, 90), r=4,
              inside=lambda x, y: not in_ellipse(0, 0, 100, 76)(x, y))
    M.lighting(sun_rot=(50, 0, 60), sky=(0.52, 0.68, 0.95), sun_e=5.0)
    return M, ['Wrogowie biegna 2 okrazenia po biezni wokol srodka - SREDNIA',
               'Wieze stawiasz na murawie w srodku albo na trybunach-blokach',
               'Baza: oltarz Zeusa na srodku stadionu',
               'Dyskobol, wazy, obozy zawodnikow, gaje oliwne']


# ====================================================================== WYSPA KIRKE (srednia)
def circe():
    M = MapScene('WyspaKirke', 'Wyspa Kirke', 'SREDNI - kladki nad bagnem, 2 lodzie', (230, 180))
    M.water(color=(0.10, 0.20, 0.18))
    islets = [(-80, 50, 24, 18), (-70, -40, 26, 20), (0, 0, 30, 24), (70, 50, 22, 16), (78, -46, 26, 20), (0, 70, 18, 12)]
    for k, (cx, cy, rx, ry) in enumerate(islets):
        M.ground(blob(cx, cy, rx, ry, seed=50 + k, amp=0.2), 'grass_swamp', z=0.3, depth=4, cliff_tex='swamp_mud',
                 name=f'islet{k}')
    A = [(-118, 70), (-80, 50), (-40, 26), (0, 0)]
    B = [(118, -66), (78, -46), (40, -22), (0, 0)]
    Cc = [(0, 0), (0, 34), (0, 64)]
    M.path(A, 7, 'boardwalk_old', z=0.6, label='Kladka A', color=(255, 90, 60), curb='wood_dark')
    M.path(B, 7, 'boardwalk_old', z=0.6, label='Kladka B', color=(255, 170, 40), curb='wood_dark')
    M.path(Cc, 8, 'boardwalk', z=0.6, label='Wspolna', color=(255, 60, 200), curb='wood_dark')
    M.place('lodz_charona', -122, 74, -0.8, 60, 1.0)
    M.place('lodz_rybacka', 122, -70, -0.8, 240, 1.2)
    M.label(-110, 84, 'SPAWN A (lodz)', (255, 140, 120))
    M.label(110, -82, 'SPAWN B (lodz)', (255, 200, 120))
    M.place('swiatynia_jonska', 0, 74, 0.3, 0, 0.5)
    M.label(0, 90, 'BAZA: Palac Kirke', (140, 220, 255))
    M.place('kociol_lawy', 0, 10, 0.3, 0, 1.0)
    M.place('krysztaly_lodu', -76, 50, 0.3, 0, 0.8) if False else None
    for cx, cy, rx, ry in islets:
        M.scatter(('drzewo_kwitnace', 'krzew_ciemny', 'grzyby', 'trzcina', 'kwiaty', 'pniak', 'drzewo_figowe',
                   'asfodele', 'ul_slomiany'), 9, (cx - rx, cy - ry, cx + rx, cy + ry), r=3, z=0.3,
                  inside=in_ellipse(cx, cy, rx * 0.8, ry * 0.8))
    M.scatter(('lilie_wodne', 'trzcina'), 30, (-115, -88, 115, 88), r=3, z=-0.8)
    M.lighting(sun_rot=(80, 0, -100), sun_col=(0.95, 0.6, 0.85), sun_e=3.0, sky=(0.45, 0.3, 0.55), sky_e=0.7)
    return M, ['Archipelag wysepek na bagnie, sciezki to drewniane kladki - SREDNIA',
               '2 lodzie z wrogami, kladki lacza sie na srodkowej wyspie',
               'Wieze tylko na wysepkach (mniej miejsca), woda dookola',
               'Magiczny zmierzch (fiolet), grzyby, asfodele, kociol czarownicy']


# ====================================================================== TERMOPILE (trudna)
def thermopylae():
    M = MapScene('Termopile', 'Termopile', 'TRUDNY - waski wawoz miedzy gorami a morzem', (230, 180))
    M.water(color=(0.04, 0.3, 0.38))
    M.ground([(-120, 90), (120, 90), (120, -30), (-120, -10)], 'grass_dry', z=0, depth=8, cliff_tex='cliff', name='pass')
    for k, x in enumerate(range(-110, 120, 22)):
        M.place('blok_klifu', x, 72, 0, k * 40, 1.5)
        M.block(x, 72, 14)
    A = [(-118, 30), (-60, 30), (-40, 10), (0, 10)]
    B = [(-118, 0), (-70, 0), (-40, 10)]
    Cc = [(0, 10), (60, 6), (90, 18), (112, 18)]
    M.path(A, 9, 'via_warm', label='Sciezka A', color=(255, 90, 60))
    M.path(B, 9, 'via_warm', label='Sciezka B (plaza)', color=(255, 170, 40))
    M.path(Cc, 9, 'via_warm', label='Wawoz', color=(255, 60, 200))
    M.place('namiot_dowodcy', -110, 50, 0, 0, 0.8)
    M.label(-100, 44, 'SPAWN A i B (oboz Persow)', (255, 140, 120))
    M.place('mur_z_wieza', 100, 38, 0, 0, 0.7)
    M.label(100, 4, 'BAZA: Spartanski mur', (140, 220, 255))
    M.place('palisada', 40, 30, 0, 0, 1.0)
    M.place('palisada', 40, -12, 0, 0, 1.0)
    M.place('stos_tarcz', 70, 30, 0, 0, 1.0)
    M.place('trofeum', 20, 34, 0, 0, 1.0)
    M.place('pole_bitwy', -10, -6, 0, 0, 1.4)
    M.place('pole_bitwy', 26, 22, 0, 0, 1.2)
    M.scatter(('skaly_grupa', 'glaz_cieply', 'kepa_trawy_sucha', 'kamyki_cieple', 'drzewo_oliwne', 'sztandar',
               'stojak_broni', 'ognisko'), 50, (-115, -20, 115, 60), r=3.5)
    for x, y, r in ((-60, -60, 20), (0, -70, -10), (60, -56, 30)):
        M.place('trirema_biala', x, y, -1.5, r, 1.0)
    M.place('gory_tlo', 0, 190, 0, 0, 1.6)
    M.lighting(sun_rot=(48, 0, 160), sun_col=(1.0, 0.9, 0.78), sun_e=4.6, sky=(0.62, 0.7, 0.85))
    return M, ['Waski pas ladu: klify od polnocy, morze od poludnia - TRUDNA',
               '2 sciezki z obozu Persow, szybko lacza sie w jeden wawoz',
               'Bardzo malo miejsca na wieze przy sciezce',
               'Pole bitwy: wlocznie, tarcze, palisady, trofeum; flota w tle']


# ====================================================================== MURY TROI (trudna)
def troy():
    M = MapScene('MuryTroi', 'Mury Troi', 'TRUDNY - dwa szturmy na brame miasta', (230, 180))
    M.water(color=(0.04, 0.32, 0.4))
    M.ground([(-120, 92), (120, 92), (120, -60), (-120, -60)], 'grass_dry', z=0, depth=6, cliff_tex='cliff', name='plain')
    M.ground([(-120, -60), (120, -60), (120, -80), (-120, -80)], 'sand', z=-0.2, depth=3, cliff_tex='sand', name='beach')
    M.plateau(0, 70, 120, 26, 4.0, 'paving_large', 'wall_cyclopean', seed=61, name='citadel')
    A = [(-100, -70), (-100, -30), (-50, -30), (-50, 10), (-14, 10), (0, 40)]
    B = [(100, -70), (100, -20), (50, -20), (50, 20), (14, 20), (0, 40)]
    M.path(A, 9, 'dirt_ruts', label='Szturm A', color=(255, 90, 60))
    M.path(B, 9, 'dirt_ruts', label='Szturm B', color=(255, 170, 40))
    for x in (-100, 100):
        M.place('trirema_bez_zagla', x, -86, -1.2, 0, 1.0)
    M.label(-100, -48, 'SPAWN A (statki Achajow)', (255, 140, 120))
    M.label(100, -48, 'SPAWN B (statki Achajow)', (255, 200, 120))
    M.place('brama_luk', 0, 46, 0, 0, 1.0)
    M.label(0, 30, 'BAZA: Brama Skajska', (140, 220, 255))
    for x in (-60, -30, 30, 60):
        M.place('mur_z_wieza', x, 52, 4.0 - 4.0, 0, 0.7)
        M.block(x, 52, 14)
    M.place('kon_trojanski', -24, 20, 0, 30, 1.6)
    M.place('wieza_oblezenicza', 70, 0, 0, -20, 0.8)
    M.place('katapulta', -70, -10, 0, 20, 1.2)
    M.place('katapulta', 74, -40, 0, -10, 1.2)
    for x, y in ((-90, -48), (-60, -50), (60, -50), (90, -46), (-20, -46), (20, -46)):
        M.place('namiot_wojskowy', x, y, 0, M.rnd.uniform(0, 360), 1.0)
    M.place('namiot_dowodcy', 0, -40, 0, 0, 0.8)
    M.scatter(('ognisko', 'sztandar', 'stojak_broni', 'beczki', 'skrzynie_stos', 'stos_tarcz', 'pole_bitwy', 'trofeum',
               'kepa_trawy_sucha', 'drzewo_oliwne'), 60, (-115, -55, 115, 40), r=4)
    M.place('dom_grecki_pietrowy', -40, 76, 4.0, 0, 0.8)
    M.place('dom_grecki_pietrowy', 40, 76, 4.0, 180, 0.8)
    M.place('swiatynia_jonska', 0, 80, 4.0, 0, 0.45)
    M.lighting(sun_rot=(60, 0, -120), sun_col=(1.0, 0.82, 0.6), sun_e=4.0, sky=(0.75, 0.62, 0.55), sky_e=0.7)
    return M, ['2 sciezki z plazy (statki Achajow) do bramy Troi - TRUDNA',
               'Sciezki biegna rownolegle i lacza sie dopiero pod brama',
               'Oboz oblegajacych: namioty, katapulty, wieza oblezenicza, kon trojanski',
               'Mury cyklopowe z wiezami, miasto na wzgorzu, morze na poludniu']


# ====================================================================== ZATOPIONA ATLANTYDA (trudna)
def atlantis():
    M = MapScene('ZatopionaAtlantyda', 'Zatopiona Atlantyda', 'TRUDNY - trzy groble nad laguna', (230, 180))
    M.water(color=(0.02, 0.45, 0.55), z=-0.6)
    M.ground(blob(0, 0, 116, 88, seed=71, amp=0.08), 'sand_white', z=-3.0, depth=6, cliff_tex='rock_white', name='lagoon_floor')
    for k, (cx, cy, r) in enumerate(((0, 0, 26), (-70, 46, 16), (70, 46, 16), (-74, -50, 18), (74, -50, 18))):
        M.ground(blob(cx, cy, r, r * 0.8, seed=80 + k, amp=0.12), 'paving_marble', z=0.4, depth=4, cliff_tex='blocks_marble',
                 name=f'ruin{k}')
    A = [(0, 88), (0, 50), (0, 12)]
    B = [(-118, 0), (-60, 0), (-24, 0)]
    Cc = [(118, -10), (60, -10), (24, -4)]
    for pts, lab, col in ((A, 'Grobla A', (255, 90, 60)), (B, 'Grobla B', (255, 170, 40)), (Cc, 'Grobla C', (255, 60, 200))):
        M.path(pts, 8, 'mosaic_waves', z=0.5, label=lab, color=col, curb='blocks_marble')
    M.label(0, 92, 'SPAWN A (morska brama)', (255, 140, 120))
    M.label(-104, 12, 'SPAWN B', (255, 200, 120))
    M.label(104, 2, 'SPAWN C', (255, 140, 220))
    M.place('fontanna_posejdona', 0, -6, 0.4, 0, 0.9)
    M.label(0, -30, 'BAZA: Tron Posejdona (srodek)', (140, 220, 255))
    for cx, cy in ((-70, 46), (70, 46), (-74, -50), (74, -50)):
        M.place('kolumna_zlamana', cx - 6, cy, 0.4, 0, 0.8)
        M.place('kolumna_jonska', cx + 6, cy, 0.4, 0, 0.8)
        M.place('zatopiony_posag', cx, cy - 6, 0.4, M.rnd.uniform(0, 360), 0.8)
    M.place('trojzab_posejdona', 0, 24, 0.4, 0, 1.0)
    M.scatter(('koral', 'wodorosty', 'babelki', 'zatopiony_posag', 'kolumna_przewrocona', 'muszle', 'skrzynia_skarbow',
               'gruz_marmurowy'), 70, (-112, -84, 112, 84), r=3.5, z=-3.0, margin_path=1)
    M.lighting(sun_rot=(30, 0, 30), sun_col=(0.9, 1.0, 1.0), sun_e=4.5, sky=(0.45, 0.75, 0.9), sky_e=1.0)
    return M, ['Laguna z ruinami pod woda, sciezki to marmurowe groble - TRUDNA',
               '3 krotkie groble z 3 kierunkow zbiegaja sie do srodka',
               'Wieze na wysepkach-ruinach i plyciznach',
               'Koralowce, wodorosty, zatopione posagi, skrzynia skarbow (easter egg)']


# ====================================================================== LODOWE WROTA BOREASZA (trudna)
def boreas():
    M = MapScene('LodoweWrotaBoreasza', 'Lodowe Wrota Boreasza', 'TRUDNY - dwie spirale przez sniezyce', (230, 180))
    M.ground(blob(0, 0, 118, 90, seed=91, amp=0.08), 'snow', z=0, depth=40, cliff_tex='cliff_grey', name='snowfield')
    M.ground([(-125, -12), (125, -4), (125, -16), (-125, -24)], 'ice', z=-0.2, depth=1, cliff_tex='ice', name='frozen_river')
    A = [(-110, 74), (-40, 74), (-40, 40), (-80, 40), (-80, 10), (-20, 10), (-10, -40)]
    B = [(110, 74), (40, 74), (40, 40), (80, 40), (80, 10), (20, 10), (10, -40)]
    M.path(A, 8, 'snow_path', label='Sciezka A', color=(255, 90, 60), curb='blocks_grey')
    M.path(B, 8, 'cobble_snowy', label='Sciezka B', color=(255, 170, 40), curb='blocks_grey')
    M.place('brama_portal_zielony', -110, 74, 0, 90, 0.8)
    M.place('brama_portal_zielony', 110, 74, 0, -90, 0.8)
    M.label(-104, 86, 'SPAWN A', (255, 140, 120))
    M.label(104, 86, 'SPAWN B', (255, 200, 120))
    M.place('swiatynia_ruiny', 0, -64, 0, 0, 0.7)
    M.label(0, -86, 'BAZA: Swiatynia Boreasza', (140, 220, 255))
    M.place('most_kamienny', -14, -14, -0.4, 0, 0.9)
    M.place('most_kamienny', 14, -12, -0.4, 0, 0.9)
    M.scatter(('sosna_osniezona', 'sosna_osniezona_2', 'krysztaly_lodu', 'zamarzniety_posag', 'sople_skala', 'zaspa',
               'glaz_bialy', 'skaly_grupa'), 90, (-115, -88, 115, 88), r=4, inside=in_ellipse(0, 0, 112, 84))
    for x, y in ((-220, 150), (0, 230), (220, 150)):
        M.place('szczyt_osniezony', x, y, -40, 0, 1.6)
    M.lighting(sun_rot=(20, 0, 60), sun_col=(0.85, 0.92, 1.0), sun_e=3.0, sky=(0.75, 0.82, 0.92), sky_e=1.2)
    return M, ['2 sciezki w ksztalcie spirali, zamarznieta rzeka przez srodek - TRUDNA',
               'Snieg, lod, osniezone jodly, krysztaly, zamarzniete posagi',
               'Ruiny swiatyni Boreasza jako baza, 2 mosty nad lodem',
               'Mrozne swiatlo, sniezyca (efekt czastek w Robloxie)']


# ====================================================================== BRAMY HADESU (koszmar)
def hades():
    M = MapScene('BramyHadesu', 'Bramy Hadesu', 'KOSZMAR - trzy sciezki przez Styks', (230, 180))
    M.water(color=(0.02, 0.06, 0.05), z=-1.5)
    M.ground(blob(0, 0, 118, 88, seed=101, amp=0.12), 'ash', z=0, depth=20, cliff_tex='basalt', name='cavern')
    M.ground([(-125, 0), (125, 10), (125, -6), (-125, -16)], 'water', z=-0.8, depth=0.3, cliff_tex='basalt', name='styx')
    A = [(-110, 70), (-60, 70), (-40, 30), (-30, -8), (-10, -50)]
    B = [(0, 88), (0, 40), (8, -8), (0, -50)]
    Cc = [(110, 70), (60, 60), (40, 26), (30, -6), (10, -50)]
    M.path(A, 8, 'cobble_dark', label='A', color=(255, 90, 60), curb='blocks_dark')
    M.path(B, 8, 'obsidian_path', label='B', color=(255, 170, 40), curb='blocks_dark')
    M.path(Cc, 8, 'cobble_dark', label='C', color=(255, 60, 200), curb='blocks_dark')
    for x, y in ((-110, 70), (0, 88), (110, 70)):
        M.place('brama_kosci', x, y, 0, 0, 0.7)
    M.label(-100, 82, 'SPAWN A', (255, 140, 120))
    M.label(14, 94, 'SPAWN B', (255, 200, 120))
    M.label(100, 82, 'SPAWN C', (255, 140, 220))
    M.place('mauzoleum', 0, -68, 0, 0, 1.2)
    M.label(0, -88, 'BAZA: Palac Hadesa', (140, 220, 255))
    M.place('posag_cerbera', -24, -50, 0, 30, 1.0)
    M.place('helm_hadesa', 24, -50, 0, 0, 1.0)
    for x in (-30, 8, 30):
        M.place('most_kamienny', x, -4, -1.2, 0, 0.8)
    M.place('lodz_charona', -70, -6, -0.6, 90, 1.2)
    M.scatter(('asfodele', 'pochodnia_duchow', 'szkielet', 'kosci', 'nagrobek', 'nagrobek_2', 'otwarty_grob',
               'czaszka_na_palu', 'klatka', 'kolumny_bazaltowe', 'drzewo_spalone', 'lancuchy_mur', 'obsydian'), 90,
              (-115, -85, 115, 85), r=3.5, inside=in_ellipse(0, 0, 110, 82))
    M.lighting(sun_rot=(70, 0, 0), sun_col=(0.5, 1.0, 0.7), sun_e=0.5, sky=(0.03, 0.06, 0.05), sky_e=0.6)
    return M, ['3 krotkie sciezki z kostnych bram, kazda przechodzi przez Styks - KOSZMAR',
               'Sciezki zbiegaja sie tuz przed palacem Hadesa',
               'Laki asfodeli, zielone ognie duchow, Cerber, lodz Charona',
               'Ciemnosc i zielona mgla, ciemna woda Styksu']


MAPS14 = [piraeus, agora, hesperides, knossos, delphi, olympia, circe, thermopylae, troy, olympus, atlantis, boreas,
          hades, hephaestus]
