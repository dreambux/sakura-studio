"""Mapa 15: Brama Lwow - pokaz nowych modeli (domy z Olintu, posagi, bron) i platform pod jednostki."""
import math

from mathutils import Vector

from .mapscene import MapScene
from .m_maps import blob, in_ellipse


def _river_x(y, side):
    return side * 7.5 + 3.5 * math.sin(y / 17.0) + 1.5 * math.sin(y / 7.0 + 1.0)


def brama_lwow():
    M = MapScene('BramaLwow', 'Brama Lwow', 'SREDNI - waz przez miasto, most i gimnazjon', (236, 180))
    M.water(color=(0.07, 0.36, 0.42))
    # dwa brzegi rzeki (woda widoczna w szczelinie miedzy nimi)
    ys = [88 - k * 4 for k in range(45)]
    west = [(-118, 88)] + [(_river_x(y, -1), y) for y in ys] + [(-118, -88)]
    east = [(118, -88)] + [(_river_x(y, 1), y) for y in reversed(ys)] + [(118, 88)]
    west = list(reversed(west)) if False else west
    M.ground(west, 'grass_dry', z=0, depth=6, cliff_tex='cliff_white', name='west')
    M.ground(east, 'grass_meadow', z=0, depth=6, cliff_tex='cliff_white', name='east')
    # miasto: ubite place i bruk pod zabudowa
    M.ground(blob(-74, -48, 32, 22, seed=3, amp=0.06), 'ground_scattered', z=0.05, depth=1, cliff_tex='dirt', name='town_a')
    M.ground(blob(-66, 8, 22, 22, seed=4, amp=0.06), 'paving_sandstone', z=0.05, depth=1, cliff_tex='dirt', name='agora')
    M.ground(blob(58, 0, 20, 34, seed=5, amp=0.06), 'gravel_warm', z=0.05, depth=1, cliff_tex='dirt', name='gym')
    # akropol (baza)
    M.plateau(86, 72, 22, 13, 4.0, 'paving_marble', 'cliff_white', seed=9, name='acropolis')

    route = [(-40, -92), (-40, -22), (-92, -22), (-92, 38), (-12, 38), (34, 38), (34, -44), (84, -44),
             (84, 54)]
    M.path(route, 9, 'via_limestone', label='Sciezka', curb='blocks')
    M.label(-18, -66, 'SPAWN: Brama Poludniowa', (255, 140, 120))
    M.place('brama_luk', -40, -84, 0, 0, 0.9)
    for x in (-62, -84, -106, -18):
        M.place('mur', x, -84, 0, 0, 1.0)
        M.block(x, -84, 7)
    M.place('most_kamienny', 0, 38, -0.2, 90, 1.0)
    M.label(0, 50, 'Most nad rzeka', (200, 230, 255))
    # baza
    M.place('swiatynia_dorycka', 88, 74, 4.0, 0, 0.62)
    M.place('schody', 84, 58, 0, 0, 0.9)
    M.place('sfinks_naksyjski', 66, 72, 4.0, 0, 0.75)
    M.place('posag_lwa', 74, 52, 0.05, 90, 0.8)
    M.place('posag_lwa', 95, 52, 0.05, 90, 0.8)
    M.label(88, 88, 'BAZA: Swiatynia Ateny na Akropolu', (140, 220, 255))

    # ---------------------------------------------------- platformy pod jednostki (14)
    plats = [('platforma_okragla', -56, -63, 0), ('platforma_fasolka', -24, -60, 90), ('platforma_owalna', -73, -6, 0),
             ('platforma_mala', -106, 8, 0), ('platforma_dluga', -60, 53, 0), ('platforma_l', -30, 22, 180),
             ('platforma_wysoka', 18, 54, 0), ('platforma_schody', 21, 2, 90), ('platforma_ruiny', 49, 20, 0),
             ('platforma_marmurowa', 58, -27, 0), ('platforma_polksiezyc', 60, -64, 180),
             ('platforma_pietrowa', 103, -2, 90), ('platforma_trawiasta', 67, 32, 0), ('platforma_trojkatna', 103, -64, 0)]
    for k, (p, x, y, r) in enumerate(plats):
        M.place(p, x, y, 0.02, r, 1.0)
        M.block(x, y, 9)
    M.label(-56, -52, 'P1', (255, 230, 120))
    M.label(18, 66, 'Wieza snajperow', (255, 230, 120))

    # ---------------------------------------------------- miasto (domy z Olintu)
    houses = [('dom_grecki', -94, -50, 0, 0.72), ('dom_grecki_pietrowy', -72, -44, 180, 0.72),
              ('dom_ochra', -100, -72, 0, 0.8), ('dom_grecki', -74, -70, 0, 0.62), ('dom_cykladzki', -104, -32, 90, 0.6),
              ('dom_ochra', -78, 18, 0, 0.9), ('dom_cykladzki', -54, -6, 90, 0.75),
              ('dom_grecki_pietrowy', -98, 66, 180, 0.72), ('dom_grecki', -38, 68, 180, 0.72),
              ('dom_ochra', -70, 76, 180, 0.85), ('dom_grecki', -104, -6, 90, 0.6)]
    for p, x, y, r, s in houses:
        M.place(p, x, y, 0.06, r, s)
        M.block(x, y, 9.5 * s / 0.72)
    M.place('fontanna', -60, 22, 0.06, 0, 0.8)
    M.place('posag_bogini', -50, 12, 0.06, 200, 0.6)
    M.place('herma', -84, -30, 0.06, 0, 0.6)
    M.place('herma', -48, -30, 0.06, 0, 0.6)
    M.place('posag_lwa', -104, -88 + 2, 0.05, 0, 0.55) if False else None
    for b in ((-60, 22, 5), (-50, 12, 3), (-84, -30, 2), (-48, -30, 2)):
        M.block(*b)
    M.label(-66, 30, 'Agora z fontanna', (255, 255, 255))

    # ---------------------------------------------------- oboz przy moscie (bron)
    for p, x, y, r in (('stojak_broni', 18, -26, 90), ('stos_tarcz', 17, -44, 0), ('trofeum', 20, -66, 0),
                       ('pole_bitwy', 22, -82, 0), ('namiot_wojskowy', -22, -88 + 6, 0)):
        M.place(p, x, y, 0.03, r, 0.9)
        M.block(x, y, 5)
    M.label(20, -36, 'Oboz hoplitow', (255, 255, 255))

    # ---------------------------------------------------- gimnazjon i ogrod posagow
    for p, x, y, r, s in (('dyskobol', 46, -6, 200, 0.7), ('posag_konia', 70, 6, 120, 0.7),
                          ('posag_wojownika', 44, 2 + 40, 200, 0.6), ('posag_zloty', 72, -14, 160, 0.6),
                          ('posag_apollina', 50, -40 + 30, 180, 0.55), ('posag_pegaza', 102, 30, 230, 0.6),
                          ('kora_posag', 76, 18, 200, 0.6)):
        M.place(p, x, y, 0.06, r, s)
        M.block(x, y, 4)
    M.label(58, -18, 'Gimnazjon - ogrod posagow', (255, 255, 255))

    # ---------------------------------------------------- easter eggi
    M.place('skrzynia_skarbow', 112, 84, 0.02, 200, 0.8)
    M.block(112, 84, 3)
    M.place('sowa_ateny', -114, 84, 0.02, 160, 0.6)
    M.block(-114, 84, 2)

    # ---------------------------------------------------- rzeka: lodzie, pomost; pola na polnocnym zachodzie
    M.place('lodz_rybacka', -1, -30, -0.9, 90, 0.7)
    M.place('lodz_rybacka', 2, 70, -0.9, 80, 0.6)
    M.place('pomost', -12, -46, -0.3, 90, 0.7)
    M.place('pole_pszenicy', -64, 84, 0.02, 0, 1.0) if False else None
    for p, x, y, r in (('pole_pszenicy', -24, 84, 0), ('stog_siana', -12, 74, 0), ('plot_drewniany', -30, 78, 0),
                       ('ul_slomiany', -112, 46, 0), ('ul_slomiany', -110, 52, 0), ('prasa_oliwna', -108, 24, 90),
                       ('piec_chlebowy', -86, -64, 0), ('zarna', -60, -78 + 4, 0), ('studnia', -88, 2, 0),
                       ('kapliczka', 30, 64, 180), ('zegar_sloneczny', 44, 52, 0), ('drogowskaz', -28, -24, 0),
                       ('koksownik', 76, 60, 0), ('koksownik', 94, 60, 0)):
        M.place(p, x, y, 0.03, r, 0.9)
        M.block(x, y, 3)
    # ---------------------------------------------------- przyroda
    river = lambda x, y: abs(x - _river_x(y, 0) * 0) > 13
    M.scatter(('trzcina', 'lilie_wodne', 'kepa_trawy'), 30, (-14, -86, 14, 86), r=2.0,
              inside=lambda x, y: abs(x - (_river_x(y, -1) + _river_x(y, 1)) / 2) < 8 and abs(y - 38) > 8,
              margin_path=1.0, z=-0.6)
    M.scatter(('drzewo_oliwne', 'drzewo_oliwne_2', 'drzewo_oliwne_3', 'cyprys', 'cyprys_2', 'krzew_oleander',
               'krzew_oliwny', 'lawenda', 'kwiaty', 'glaz', 'glaz_2', 'kamyki', 'skaly_grupa', 'kepa_trawy_sucha',
               'drzewo_figowe', 'granatowiec', 'asfodele', 'drzewo_cytrynowe', 'krzew', 'kepa_trawy',
               'sosna_parasolowa'), 230, (-116, -86, 116, 86), r=3.5,
              inside=lambda x, y: abs(x - (_river_x(y, -1) + _river_x(y, 1)) / 2) > 12)
    M.scatter(('amfory_grupa', 'skrzynie_stos', 'beczki', 'kosz_owocow', 'lampa_oliwna', 'worki'), 18,
              (-110, -76, -30, 80), r=2.5)
    M.scatter(('glaz', 'kamyki', 'kepa_trawy_sucha', 'kwiaty'), 60, (-116, -86, 116, 86), r=1.8, margin_path=1.5,
              inside=lambda x, y: abs(x - (_river_x(y, -1) + _river_x(y, 1)) / 2) > 11)
    M.lighting(sun_rot=(48, 0, 40), sky=(0.55, 0.68, 0.92), sky_e=0.9, sun_e=5.0)
    legend = ['SREDNI: jedna sciezka, 9 zakretow - waz przez miasto, most i gimnazjon',
              '14 skal-platform (P) dla jednostek przy zakretach, w tym wieza snajperow',
              'Miasto: domy z dziedzincem (Olint), agora z fontanna, hermy',
              'Most nad rzeka = waskie gardlo; za nim oboz hoplitow z bronia',
              'Baza: Akropol ze swiatynia, Sfinks Naksyjczykow, para lwow',
              'Easter egg: skrzynia skarbow w rogu NE, sowa Ateny w rogu NW']
    return M, legend
