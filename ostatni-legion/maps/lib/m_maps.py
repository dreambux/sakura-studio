"""4 koncepty map (uklad 1 stud = 1 jednostka; X w prawo, Y na polnoc, Z w gore)."""
import math

from .mapscene import MapScene


def blob(cx, cy, rx, ry, n=36, seed=0, amp=0.12):
    from mathutils import Vector, noise
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        r = 1 + amp * noise.noise(Vector((math.cos(a) * 1.7 + seed, math.sin(a) * 1.7, seed * 0.37)))
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return pts


def in_ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1


# ====================================================================== 1. ZATOKA PIREUSU (latwa)
def piraeus():
    M = MapScene('ZatokaPireusu', 'Zatoka Pireusu', 'LATWY - jedna dluga sciezka', (230, 180))
    M.water(color=(0.03, 0.36, 0.42))
    M.ground(blob(0, 0, 112, 84, seed=1, amp=0.08), 'sand_white', z=0.0, depth=8, cliff_tex='rock_warm', name='beach')
    M.ground(blob(4, 2, 100, 72, seed=2, amp=0.08), 'grass_dry', z=0.06, depth=1, cliff_tex='sand_white', name='grass')
    M.ground([(-58, 34), (-24, 34), (-24, 8), (-58, 8)], 'paving', z=0.09, depth=1, cliff_tex='blocks', name='agora')
    M.ground([(42, -30), (96, -30), (96, -62), (42, -62)], 'paving_marble', z=0.1, depth=1, cliff_tex='blocks',
             name='temple_square')
    route = [(-108, 58), (-80, 58), (-66, 56), (-66, 26), (-36, 26), (-36, 52), (-4, 52), (-4, 16), (26, 16),
             (26, 50), (60, 50), (60, 12), (14, -14), (14, -46), (52, -46)]
    M.path(route, 9, 'cobble', label='Sciezka 1', color=(255, 90, 60))
    # spawn: pomost z widmowa trirema i brama z portalem
    M.place('pomost', -112, 58, 0, 90, 1.6)
    M.place('trirema_czarna', -122, 76, -1.5, 90, 1.0)
    M.place('brama_portal_czerwony', -96, 58, 0, 90, 0.8)
    M.label(-96, 68, 'SPAWN (widmowa trirema)', (255, 140, 120))
    # baza: swiatynia Posejdona
    M.place('swiatynia_dorycka', 72, -46, 0.1, 90, 0.75)
    M.block(72, -46, 22)
    M.label(72, -24, 'BAZA: Swiatynia Posejdona', (140, 220, 255))
    # port (zachod): pomosty, zacumowane statki, dzwig, amfory
    for i, y in enumerate((-10, -34, -58)):
        M.place('pomost', -112, y, 0, 90, 1.3)
        M.place('trirema_bez_zagla' if i != 1 else 'trirema', -124, y - 10, -1.5, 90, 0.9)
    M.place('lodz_rybacka', -104, -22, -1.0, 20, 1.0)
    M.place('lodz_rybacka', -100, -46, -1.0, -30, 1.0)
    M.place('dzwig_portowy', -92, -18, 0, 90, 1.0)
    for x, y in ((-90, -4), (-86, -40), (-80, -62)):
        M.place('amfory_stojak', x, y, 0, 90, 1.0)
        M.place('skrzynie_stos', x + 6, y + 4, 0, 30, 1.0)
        M.place('beczki', x + 4, y - 6, 0, 0, 1.0)
    M.place('sieci_rybackie', -94, 6, 0, 90, 1.0)
    M.place('kotwica', -84, 10, 0, 20, 1.0)
    for x, y in ((-100, 12), (-100, -28), (-98, -52)):
        M.place('pacholek', x, y, 0, 0, 1.0)
    # agora i miasto
    M.place('fontanna', -44, 20, 0.1, 0, 1.0)
    M.place('stragan', -52, 30, 0.1, 180, 0.9)
    M.place('stragan_niebieski', -30, 30, 0.1, 180, 0.9)
    M.place('stragan', -52, 12, 0.1, 0, 0.9)
    M.place('kosz_owocow', -38, 12, 0.1, 0, 1.0)
    M.place('amfory_grupa', -28, 12, 0.1, 0, 1.0)
    M.place('posag_bogini', -16, 34, 0, 180, 0.8)
    for x, y in ((-20, 70), (12, 70), (40, 68), (-48, 70), (78, 62), (-50, -14), (-30, -30), (-60, -40),
                    (90, 30), (88, 4)):
        M.place('dom_grecki' if (x + y) % 3 else 'dom_grecki_pietrowy', x, y, 0, M.rnd.choice((0, 90, 180, 270)), 0.9)
        M.block(x, y, 9)
    M.place('dom_cykladzki', -10, -34, 0, 0, 0.9)
    M.block(-10, -34, 8)
    M.plateau(40, -4, 13, 10, 3.0, 'grass_dry', 'rock_warm', seed=3)
    M.place('wiatrak', 40, -4, 3.0, 45, 0.9)
    # latarnia na skalnej wysepce
    M.plateau(118, 70, 12, 10, 2.0, 'rock_warm', 'rock_warm', seed=4, name='islet')
    M.place('latarnia_morska', 118, 70, 2.0, 0, 0.6)
    # roslinnosc
    green = ('drzewo_oliwne', 'drzewo_oliwne_2', 'cyprys', 'palma', 'krzew_oleander', 'krzew', 'opuncja',
             'kepa_trawy_sucha', 'skaly_grupa', 'lawenda', 'kwiaty', 'kamyki_cieple')
    M.scatter(green, 120, (-95, -70, 100, 75), r=4.0, inside=in_ellipse(4, 2, 96, 68))
    M.scatter(('palma', 'kepa_trawy_sucha', 'kamyki_cieple', 'glaz_cieply'), 26, (-110, -85, 112, 85), r=3,
              inside=lambda x, y: in_ellipse(0, 0, 110, 82)(x, y) and not in_ellipse(4, 2, 99, 71)(x, y))
    M.place('pochodnia', 60, -32, 0.1, 0, 1.0)
    M.place('pochodnia', 60, -60, 0.1, 0, 1.0)
    # tlo: flota i wyspy
    for x, y, r, k in ((-60, -150, 10, 'trirema'), (-10, -165, -5, 'trirema_biala'), (40, -150, 15, 'trirema'),
                       (160, -40, 80, 'trirema_biala'), (175, 20, 95, 'trirema'), (-170, 10, -80, 'trirema_biala')):
        M.place(k, x, y, -1.5, r, 1.0)
    M.place('wyspa_tlo', 260, -120, -2, 30, 1.6)
    M.place('wyspa_tlo', -280, 140, -2, 200, 2.0)
    M.place('wyspa_tlo', 60, 260, -2, 90, 1.4)
    M.lighting(sun_rot=(42, 0, 40), sky=(0.5, 0.68, 0.95), sky_e=0.9, sun_e=5.0)
    legend = ['Czerwona linia = trasa wrogow (1 sciezka, ~520 st. - latwa)',
              'Zachod: port z pomostami, triremy, dzwig, amfory',
              'Srodek: agora z fontanna i straganami, biale domy',
              'Wzgorze z wiatrakiem, latarnia na wysepce (NE)',
              'Woda dookola (mozna plywac), flota na horyzoncie']
    return M, legend


# ====================================================================== 2. LABIRYNT KNOSSOS (srednia)
def knossos():
    M = MapScene('LabiryntKnossos', 'Labirynt Knossos', 'SREDNI - dwa wejscia laczace sie', (230, 180))
    M.water(color=(0.05, 0.30, 0.40), z=-6)
    M.ground([(-125, 95), (125, 95), (125, -70), (60, -88), (-20, -84), (-125, -72)], 'grass_dry', z=0.0, depth=10,
             cliff_tex='cliff', name='land')
    M.ground([(-40, 20), (40, 20), (40, -30), (-40, -30)], 'paving_red', z=0.08, depth=1, cliff_tex='blocks',
             name='court')
    M.ground([(-25, -40), (25, -40), (25, -66), (-25, -66)], 'mosaic', z=0.1, depth=1, cliff_tex='blocks',
             name='throne_floor')
    A = [(-112, 78), (-84, 78), (-84, 46), (-58, 46), (-58, 70), (-28, 70), (-28, 30), (-10, 6)]
    B = [(112, 78), (84, 78), (84, 50), (58, 50), (58, 72), (28, 72), (28, 30), (10, 6)]
    C = [(0, 6), (0, -14), (-20, -14), (-20, -28), (0, -28), (0, -40)]
    M.path(A, 9, 'flagstone_dirt', label='Sciezka A', color=(255, 90, 60))
    M.path(B, 9, 'flagstone_dirt', label='Sciezka B', color=(255, 170, 40))
    M.path(C, 10, 'paving_red', label='Wspolny odcinek', color=(255, 60, 160))
    M.place('jaskinia', -116, 78, 0, 90, 1.0)
    M.place('jaskinia', 116, 78, 0, -90, 1.0)
    M.label(-104, 90, 'SPAWN A (jaskinia)', (255, 140, 120))
    M.label(104, 90, 'SPAWN B (jaskinia)', (255, 200, 120))
    # baza: sala tronowa
    for x in (-18, -9, 9, 18):
        M.place('kolumna_minojska', x, -44, 0.1, 0, 1.0)
    M.place('tron', 0, -58, 0.1, 0, 1.4)
    M.place('mur_fresk', -14, -68, 0.1, 0, 1.2)
    M.place('mur_fresk', 14, -68, 0.1, 0, 1.2)
    M.place('rogi_konsekracji', 0, -70, 7.5, 0, 1.2)
    M.block(0, -55, 22)
    M.label(0, -78, 'BAZA: Sala tronowa Minosa', (140, 220, 255))
    # dziedziniec
    M.place('posag_byka', 0, -6, 0.1, 90, 0.9) if False else None
    M.place('labrys_stojak', -34, -24, 0.1, 0, 1.0)
    M.place('labrys_stojak', 34, -24, 0.1, 0, 1.0)
    for x in (-38, -26, 26, 38):
        M.place('kolumna_minojska', x, 16, 0.1, 0, 0.9)
    M.place('posag_byka', -28, 0, 0.1, 0, 0.8)
    M.place('fontanna', 28, -2, 0.1, 0, 0.8)
    # palac: sciany z freskami i rogi
    for x, y, r in ((-70, 10, 0), (-70, -14, 0), (70, 10, 0), (70, -14, 0), (-52, -50, 90), (52, -50, 90)):
        M.place('mur_fresk', x, y, 0, r, 1.0)
        M.place('rogi_konsekracji', x, y, 6.3, r, 0.8)
        M.block(x, y, 7)
    # labirynt z zywoplotow (dekoracja wokol sciezek)
    for x, y, r in ((-100, 30, 0), (-100, 6, 90), (-80, 20, 0), (100, 30, 0), (100, 6, 90), (80, 20, 0),
                    (-42, 88, 0), (42, 88, 0), (-70, 92, 90), (70, 92, 90)):
        M.place('labirynt_sciana', x, y, 0, r, 1.0)
        M.block(x, y, 6)
    # magazyny pithoi
    for i in range(6):
        M.place('pithos', -108 + i * 5, -40, 0, 0, 1.0)
        M.place('pithos', 84 + i * 5, -40, 0, 0, 1.0)
    M.place('amfory_grupa', -96, -52, 0, 0, 1.0)
    M.place('amfory_grupa', 96, -52, 0, 0, 1.0)
    # gaje oliwne i roslinnosc
    M.scatter(('drzewo_oliwne', 'drzewo_oliwne_2', 'drzewo_oliwne_3'), 40, (-120, -70, 120, 92), r=5)
    M.scatter(('cyprys', 'cyprys_2', 'krzew_oliwny', 'lawenda', 'kepa_trawy_sucha', 'kamyki_cieple', 'glaz_cieply',
               'opuncja', 'winorosl', 'kwiaty'), 70, (-120, -70, 120, 92), r=3.5)
    # tlo: gory i morze z poludnia
    M.place('gory_tlo', 0, 180, 0, 0, 1.4)
    M.place('gory_tlo', -260, 120, 0, 50, 1.0)
    M.place('trirema', -60, -150, -6, 15, 1.0)
    M.place('trirema_biala', 50, -170, -6, -20, 1.0)
    M.place('wyspa_tlo', 200, -200, -8, 0, 1.6)
    M.lighting(sun_rot=(72, 0, -60), sun_col=(1.0, 0.72, 0.45), sun_e=4.0, sky=(0.95, 0.62, 0.42), sky_e=0.7)
    legend = ['Czerwona/pomaranczowa = 2 sciezki z jaskin, rozowa = wspolny odcinek',
              'Sciezki lacza sie na dziedzincu - srednia trudnosc',
              'Kolumny minojskie, freski, rogi konsekracji, labirynt z zywoplotow',
              'Gaje oliwne, magazyny pithoi, morze od poludnia (klif)',
              'Zlota godzina: niskie cieple slonce']
    return M, legend


# ====================================================================== 3. ZBOCZA OLIMPU (trudna)
def olympus():
    M = MapScene('ZboczaOlimpu', 'Zbocza Olimpu', 'TRUDNY - dwie krotkie, osobne sciezki', (230, 180))
    M.ground(blob(0, 0, 118, 90, seed=7, amp=0.07), 'grass_alpine', z=0.0, depth=60, cliff_tex='cliff_grey',
             name='summit')
    # rzeka przez srodek (woda, mozna plywac)
    M.ground([(-125, -6), (125, 4), (125, -10), (-125, -20)], 'pebbles', z=-1.5, depth=1, cliff_tex='rock',
             name='riverbed')
    river = M.ground([(-125, -7), (125, 3), (125, -9), (-125, -19)], 'water', z=-0.6, depth=0.2, cliff_tex='water',
                     name='river')
    M.ground([(-30, -40), (30, -40), (30, -86), (-30, -86)], 'paving_marble', z=0.1, depth=1, cliff_tex='blocks_marble',
             name='sanctum')
    A = [(-104, 76), (-70, 76), (-70, 30), (-50, 30), (-50, -13), (-40, -40), (-14, -50)]
    B = [(104, 76), (66, 76), (66, 40), (44, 40), (44, -2), (38, -40), (14, -50)]
    M.path(A, 9, 'paving', label='Sciezka A', color=(255, 90, 60))
    M.path(B, 9, 'paving', label='Sciezka B', color=(255, 170, 40))
    M.place('most_kamienny', -50, -12, -0.8, 0, 1.0)
    M.place('most_kamienny', 44, -3, -0.8, -3, 1.0)
    M.place('brama_portal_zielony', -100, 76, 0, 90, 0.8)
    M.place('brama_portal_zielony', 100, 76, 0, -90, 0.8)
    M.label(-100, 88, 'SPAWN A (portal)', (255, 140, 120))
    M.label(100, 88, 'SPAWN B (portal)', (255, 200, 120))
    M.place('swiatynia_jonska', 0, -64, 0.1, 0, 0.9)
    M.place('zloty_tron_zeusa', 0, -46, 0.1, 180, 0.7) if False else None
    M.block(0, -64, 20)
    M.label(0, -92, 'BAZA: Swiatynia Zeusa', (140, 220, 255))
    # sanktuaria
    M.place('tholos', -78, -50, 0, 0, 0.8)
    M.block(-78, -50, 14)
    M.place('zloty_tron_zeusa', 80, -52, 0, 0, 0.9)
    M.block(80, -52, 9)
    M.place('piorun_pomnik', 0, 30, 0, 0, 1.0)
    M.block(0, 30, 5)
    for x, y in ((-24, -40), (24, -40), (-90, 20), (90, 20), (0, 66)):
        M.place('orzel_zeusa', x, y, 0.1, 180, 0.8)
        M.block(x, y, 3)
    for x, y in ((-34, 50), (34, 50), (-104, -30), (104, -30)):
        M.place('posag_zloty', x, y, 0, M.rnd.uniform(0, 360), 0.8)
        M.block(x, y, 3)
    M.place('swiatynia_ruiny', 0, 80, 0, 0, 0.55) if False else None
    for x in (-96, -60, 60, 96):
        M.place('koksownik', x, 60, 0, 0, 1.0)
    # roslinnosc i skaly
    M.scatter(('drzewo_jesienne', 'drzewo_kwitnace', 'cyprys', 'cyprys_2', 'sosna_parasolowa', 'platan'), 45,
              (-115, -85, 115, 85), r=5, inside=in_ellipse(0, 0, 112, 84))
    M.scatter(('glaz_bialy', 'skaly_grupa', 'krzew_ciemny', 'kwiaty', 'kepa_trawy', 'kamyki', 'glaz_mech'), 70,
              (-115, -85, 115, 85), r=3, inside=in_ellipse(0, 0, 112, 84))
    M.scatter(('trzcina',), 18, (-120, -24, 120, 8), r=1.5, margin_path=1,
              inside=lambda x, y: abs(y - (-7 + x * 0.04)) < 10)
    # tlo: szczyty i morze chmur
    for x, y, s in ((-220, 160, 1.4), (0, 230, 1.8), (230, 150, 1.3), (-300, -40, 1.1), (300, -60, 1.2)):
        M.place('szczyt_osniezony', x, y, -60, M.rnd.uniform(0, 360), s)
    for k in range(26):
        a = 2 * math.pi * k / 26
        M.place('chmura_duza', math.cos(a) * 170, math.sin(a) * 140, -18 + M.rnd.uniform(-4, 4), M.rnd.uniform(0, 360),
                M.rnd.uniform(1.4, 2.2))
    M.lighting(sun_rot=(38, 0, 120), sun_col=(1.0, 0.97, 0.92), sun_e=4.6, sky=(0.62, 0.74, 0.95), sky_e=1.0)
    legend = ['2 osobne, krotkie sciezki z portali - lacza sie dopiero przy bazie',
              'Rzeka przez srodek mapy (woda, mozna plywac), 2 kamienne mosty',
              'Tholos, zloty tron Zeusa, orly, zlote posagi, piorun w skale',
              'Brak morza: mapa na szczycie, wokol morze chmur i osniezone szczyty',
              'Mniej miejsca przy sciezkach = trudniej']
    return M, legend


# ====================================================================== 4. KUZNIA HEFAJSTOSA (koszmar)
def hephaestus():
    M = MapScene('KuzniaHefajstosa', 'Kuznia Hefajstosa', 'KOSZMAR - trzy krotkie sciezki', (230, 180))
    M.water(color=(0.01, 0.05, 0.08))
    M.ground(blob(0, 0, 112, 86, seed=11, amp=0.12), 'sand_volcanic', z=0.0, depth=10, cliff_tex='basalt',
             name='island')
    M.ground(blob(0, 4, 96, 72, seed=12, amp=0.12), 'grass_ash', z=0.06, depth=1, cliff_tex='basalt', name='ash')
    M.ground([(-26, -36), (26, -36), (26, -72), (-26, -72)], 'paving_basalt', z=0.1, depth=1, cliff_tex='basalt',
             name='forge_floor')
    A = [(0, 84), (0, 50), (-16, 30), (-16, 4), (0, -10), (0, -38)]
    B = [(-106, 20), (-70, 20), (-60, -2), (-32, -2), (-12, -12), (-2, -30)]
    Cc = [(106, 34), (74, 34), (64, 10), (36, 10), (14, -14), (2, -30)]
    M.path(A, 9, 'cobble_dark', label='Sciezka A', color=(255, 90, 60))
    M.path(B, 9, 'cobble_dark', label='Sciezka B', color=(255, 170, 40))
    M.path(Cc, 9, 'cobble_dark', label='Sciezka C', color=(255, 60, 200))
    M.place('szczelina_lawy', 0, 90, 0, 90, 1.2)
    M.place('wrak_statku', -116, 30, -1.5, 70, 1.0)
    M.place('jaskinia', 110, 34, 0, -90, 1.0)
    M.label(0, 96, 'SPAWN A (szczelina lawy)', (255, 140, 120))
    M.label(-100, 34, 'SPAWN B (wrak)', (255, 200, 120))
    M.label(100, 48, 'SPAWN C (jaskinia)', (255, 140, 220))
    M.place('kuznia', 0, -58, 0.1, 0, 1.4)
    M.place('kowadlo', -12, -46, 0.1, 30, 1.2)
    M.place('kociol_lawy', 12, -46, 0.1, 0, 1.0)
    M.place('koksownik', -22, -40, 0.1, 0, 1.0)
    M.place('koksownik', 22, -40, 0.1, 0, 1.0)
    M.block(0, -55, 20)
    M.label(0, -80, 'BAZA: Kuznia Hefajstosa', (140, 220, 255))
    # strefy lawy (nie mozna tam stawiac)
    for x, y in ((-50, 40), (48, 52), (-70, -40), (60, -34)):
        M.place('jeziorko_lawy', x, y, 0.05, 0, 1.6)
        M.block(x, y, 9)
    M.place('talos', -84, -8, 0, 60, 0.7) if False else None
    M.place('talos', 74, -56, 0, -30, 0.6)
    M.block(74, -56, 8)
    M.place('mauzoleum', -76, -58, 0, 30, 0.9)
    M.block(-76, -58, 9)
    for x, y in ((-40, 70), (-30, 62), (-48, 62)):
        M.place('nagrobek' if x % 2 else 'nagrobek_2', x, y, 0, M.rnd.uniform(-20, 20), 1.0)
    M.place('otwarty_grob', -36, 76, 0, 0, 1.0)
    M.place('kosci', 30, 60, 0, 0, 1.0)
    M.scatter(('skala_wulkaniczna', 'skala_wulkaniczna_grupa', 'kolumny_bazaltowe', 'obsydian', 'dymiacy_otwor',
               'drzewo_spalone', 'kosci', 'gruz_marmurowy', 'kolumna_zlamana', 'kolumna_przewrocona'), 80,
              (-105, -80, 105, 80), r=4, inside=in_ellipse(0, 4, 94, 70))
    M.scatter(('szczelina_lawy',), 6, (-90, -70, 90, 70), r=7, inside=in_ellipse(0, 4, 90, 66))
    # tlo: wulkan i plonace wraki
    M.place('wulkan_tlo', 0, 260, -2, 0, 1.6)
    for x, y, r in ((-150, -60, 30), (140, -110, -40), (-60, -160, 10), (180, 60, 100)):
        M.place('trirema_czarna', x, y, -2.5, r, 1.0)
    M.place('wrak_statku', 90, -120, -1.5, 30, 1.2)
    M.lighting(sun_rot=(55, 0, -150), sun_col=(0.8, 0.8, 1.0), sun_e=2.4, sky=(0.16, 0.12, 0.18), sky_e=1.1)
    legend = ['3 krotkie sciezki (szczelina lawy, wrak, jaskinia) - KOSZMAR',
              'Sciezki zbiegaja sie tuz przed kuznia - malo czasu na reakcje',
              'Jeziorka lawy blokuja stawianie wiez (strefy zakazane)',
              'Talos, grobowiec, groby nieumarlych, bazalt, obsydian, fumarole',
              'Noc, czerwona lawa, wulkan w tle, czarne triremy']
    return M, legend


MAPS = [piraeus, knossos, olympus, hephaestus]
