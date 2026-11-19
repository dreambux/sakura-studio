/* Szamka: dane startowe (lokale, menu, ustawienia).
   Zmiany robione w panelu admina zapisują się w przeglądarce. Zakładka „Dane” w panelu
   potrafi wygenerować nową wersję tego pliku, żeby zmiany zobaczył każdy, kto wejdzie na stronę. */
(function () {
  'use strict';

  function pary(lista) {
    return (lista || []).map(function (p) { return { name: p[0], price: p[1] }; });
  }
  /* danie: [nazwa, opis, cena, { pop: popularne, v: warianty, e: dodatki }] */
  function lokal(id, name, cfg, menu) {
    var r = {
      id: id, name: name, kitchen: '', cuisines: [], art: 'pizza', color: '#2E6B4F', cover: '', logo: '',
      rating: 4.5, reviews: 100, timeMin: 30, timeMax: 45, fee: 4.99, minOrder: 30, freeFrom: 0,
      open: true, opensAt: '', badge: '', sponsored: false, isNew: false, hidden: false, address: ''
    };
    Object.keys(cfg).forEach(function (k) { r[k] = cfg[k]; });
    r.menu = menu.map(function (kat, ci) {
      return {
        id: id + '-k' + ci, name: kat[0],
        items: kat[1].map(function (d, ii) {
          var o = d[3] || {};
          return {
            id: id + '-' + ci + '-' + ii, name: d[0], desc: d[1] || '', price: d[2], img: '',
            popular: !!o.pop, variants: pary(o.v), extras: pary(o.e)
          };
        })
      };
    });
    return r;
  }

  var pizzaV = [['32 cm', 0], ['42 cm', 12]];
  var pizzaE = [['Dodatkowa mozzarella', 6], ['Szynka parmeńska', 9], ['Rukola', 4], ['Sos czosnkowy', 3]];
  var kebabV = [['Standardowy', 0], ['Duży', 7]];
  var kebabE = [['Podwójne mięso', 9], ['Ser feta', 4], ['Frytki do środka', 4], ['Jalapeño', 2]];
  var kebabS = [['Sos czosnkowy', 0], ['Sos ostry', 0], ['Sos mieszany', 0]];
  var burgerV = [['Sam burger', 0], ['Zestaw z frytkami i napojem', 13]];
  var burgerE = [['Dodatkowy bekon', 6], ['Podwójny cheddar', 5], ['Jajko sadzone', 4], ['Krążki cebulowe w środku', 5]];
  var sushiE = [['Dodatkowy imbir', 3], ['Dodatkowe wasabi', 3], ['Sos teriyaki', 4], ['Pałeczki dla 4 osób', 0]];
  var pierogiV = [['Z wody', 0], ['Podsmażane', 2]];
  var pierogiE = [['Okrasa z boczku', 4], ['Cebulka zasmażana', 3], ['Śmietana', 3]];
  var ramenE = [['Dodatkowe jajko', 5], ['Dodatkowe chashu', 9], ['Dodatkowy makaron', 7], ['Olej chili', 3]];
  var curryV = [['Łagodne', 0], ['Średnio ostre', 0], ['Ostre', 0]];
  var curryE = [['Ryż basmati', 7], ['Naan maślany', 8], ['Naan czosnkowy', 9], ['Raita', 6]];
  var bowlV = [['Ryż biały', 0], ['Ryż brązowy', 0], ['Mix sałat', 0]];
  var burritoV = [['W tortilli', 0], ['Jako bowl, bez tortilli', 0]];
  var tacoE = [['Guacamole', 6], ['Ser cheddar', 4], ['Pico de gallo', 4]];

  var restaurants = [
    lokal('pizzeria-na-rogu', 'Pizzeria Na Rogu', {
      kitchen: 'Pizza, włoska, makarony', cuisines: ['pizza', 'wloska'], art: 'pizza', color: '#2E6B4F',
      rating: 4.7, reviews: 2314, timeMin: 25, timeMax: 40, fee: 4.99, minOrder: 35, badge: 'Druga pizza −50%',
      sponsored: true, address: 'ul. Hoża 41, Warszawa'
    }, [
      ['Pizza klasyczna', [
        ['Margherita', 'Sos pomidorowy, mozzarella fior di latte, świeża bazylia', 31, { pop: true, v: pizzaV, e: pizzaE }],
        ['Capricciosa', 'Sos pomidorowy, mozzarella, szynka, pieczarki, czarne oliwki', 37, { pop: true, v: pizzaV, e: pizzaE }],
        ['Salame piccante', 'Sos pomidorowy, mozzarella, pikantne salami, jalapeño', 38, { v: pizzaV, e: pizzaE }],
        ['Prosciutto e rucola', 'Mozzarella, szynka parmeńska, rukola, płatki parmezanu', 43, { pop: true, v: pizzaV, e: pizzaE }],
        ['Quattro formaggi', 'Mozzarella, gorgonzola, parmezan, ricotta', 41, { v: pizzaV, e: pizzaE }],
        ['Vegetariana', 'Cukinia, papryka, bakłażan, czerwona cebula, pomidorki', 36, { v: pizzaV, e: pizzaE }]
      ]],
      ['Pizza biała', [
        ['Bianca z gruszką', 'Śmietana, gorgonzola, gruszka, orzechy włoskie, miód', 40, { v: pizzaV, e: pizzaE }],
        ['Carbonara', 'Śmietana, boczek, żółtko, pecorino, świeży pieprz', 41, { v: pizzaV, e: pizzaE }]
      ]],
      ['Makarony', [
        ['Spaghetti aglio e olio', 'Czosnek, oliwa, chili, natka pietruszki', 29],
        ['Penne arrabbiata', 'Pikantny sos pomidorowy, czosnek, bazylia', 30],
        ['Tagliatelle z kurczakiem', 'Kurczak, szpinak, suszone pomidory, sos śmietanowy', 36]
      ]],
      ['Przystawki i sałatki', [
        ['Bruschetta (3 szt.)', 'Grzanki z pomidorami, czosnkiem i bazylią', 19],
        ['Sałatka caprese', 'Pomidory, mozzarella, bazylia, oliwa', 27],
        ['Focaccia z rozmarynem', 'Z oliwą i solą morską', 16]
      ]],
      ['Desery', [
        ['Tiramisu', 'Robione na miejscu, z mascarpone', 21, { pop: true }],
        ['Panna cotta z malinami', '', 18]
      ]],
      ['Napoje', [
        ['Lemoniada cytrynowa 0,4 l', '', 12], ['Cola 0,5 l', '', 9], ['Woda niegazowana 0,5 l', '', 6]
      ]]
    ]),

    lokal('kebab-bosfor', 'Kebab Bosfor', {
      kitchen: 'Kebab, turecka', cuisines: ['kebab'], art: 'kebab', color: '#2B3A67',
      rating: 4.5, reviews: 3870, timeMin: 20, timeMax: 35, fee: 3.99, minOrder: 25, freeFrom: 60,
      badge: 'Darmowa dostawa od 60 zł', address: 'ul. Marszałkowska 85, Warszawa'
    }, [
      ['Kebaby', [
        ['Kebab w bułce', 'Mięso wołowo-baranie albo kurczak, surówki, sos do wyboru', 24, { pop: true, v: kebabV, e: kebabE }],
        ['Kebab w tortilli', 'Zawijany, z surówkami i sosem do wyboru', 26, { pop: true, v: kebabV, e: kebabE }],
        ['Kebab na talerzu', 'Mięso, frytki, trzy surówki, dwa sosy', 34, { pop: true, e: kebabE }],
        ['Kebab box', 'Mięso i frytki w pudełku, sos do wyboru', 25, { v: kebabV, e: kebabE }],
        ['Falafel w tortilli', 'Wegetariański, z hummusem i warzywami', 25, { e: [['Ser feta', 4], ['Jalapeño', 2]] }]
      ]],
      ['Pide i lahmacun', [
        ['Pide z serem i suczukiem', 'Turecka łódeczka z pieca', 29],
        ['Lahmacun', 'Cienki placek z mielonym mięsem i ziołami', 19]
      ]],
      ['Dodatki', [
        ['Frytki', '', 11, { v: [['Małe', 0], ['Duże', 4]] }],
        ['Frytki z serem', '', 15],
        ['Falafel (5 szt.)', 'Z sosem jogurtowym', 14],
        ['Sos', '', 3, { v: kebabS }]
      ]],
      ['Desery', [['Baklawa (3 szt.)', 'Z pistacjami', 15]]],
      ['Napoje', [['Ayran 0,25 l', '', 6], ['Cola 0,5 l', '', 8], ['Woda 0,5 l', '', 5]]]
    ]),

    lokal('bulka-i-wol', 'Bułka i Wół', {
      kitchen: 'Burgery, amerykańska', cuisines: ['burgery'], art: 'burger', color: '#E9B23C',
      rating: 4.8, reviews: 1562, timeMin: 30, timeMax: 45, fee: 5.99, minOrder: 40, isNew: true,
      badge: 'Frytki gratis do zestawu', address: 'ul. Poznańska 12, Warszawa'
    }, [
      ['Burgery', [
        ['Klasyk', 'Wołowina 150 g, cheddar, sałata, pomidor, pikle, sos firmowy', 34, { pop: true, v: burgerV, e: burgerE }],
        ['Bekon i BBQ', 'Wołowina, chrupiący bekon, cheddar, cebula, sos BBQ', 38, { pop: true, v: burgerV, e: burgerE }],
        ['Blue cheese', 'Wołowina, ser pleśniowy, karmelizowana cebula, rukola', 39, { v: burgerV, e: burgerE }],
        ['Jalapeño', 'Wołowina, cheddar, jalapeño, nachos, ostry majonez', 38, { v: burgerV, e: burgerE }],
        ['Podwójny Wół', 'Dwa kotlety, podwójny cheddar, pikle, sos firmowy', 46, { pop: true, v: burgerV, e: burgerE }],
        ['Chrupiący kurczak', 'Kurczak w panierce, colesław, pikle, majonez', 33, { v: burgerV, e: burgerE }],
        ['Wege z halloumi', 'Grillowany halloumi, pieczona papryka, rukola, pesto', 35, { v: burgerV }]
      ]],
      ['Dodatki', [
        ['Frytki belgijskie', '', 13], ['Frytki z batatów', '', 16], ['Krążki cebulowe (8 szt.)', '', 15],
        ['Colesław', '', 9], ['Nuggetsy (6 szt.)', 'Z sosem do wyboru', 19, { v: [['Sos BBQ', 0], ['Sos czosnkowy', 0], ['Majonez truflowy', 2]] }]
      ]],
      ['Sosy', [['Majonez truflowy', '', 5], ['BBQ', '', 4], ['Czosnkowy', '', 4]]],
      ['Napoje', [['Lemoniada domowa 0,4 l', '', 12], ['Cola 0,33 l', '', 9], ['Shake waniliowy', '', 17]]]
    ]),

    lokal('sushi-fala', 'Sushi Fala', {
      kitchen: 'Sushi, japońska', cuisines: ['sushi', 'azjatycka'], art: 'sushi', color: '#F2A7A0',
      rating: 4.6, reviews: 986, timeMin: 40, timeMax: 60, fee: 7.99, minOrder: 60, freeFrom: 150,
      badge: '−15% na zestawy', address: 'ul. Wilcza 29, Warszawa'
    }, [
      ['Zestawy', [
        ['Mała Fala (16 szt.)', 'Futomaki z łososiem, hosomaki z ogórkiem, 2 nigiri', 59, { pop: true, e: sushiE }],
        ['Duża Fala (32 szt.)', 'Przekrój całej karty: futomaki, hosomaki, nigiri, uramaki', 109, { pop: true, e: sushiE }],
        ['Zestaw wege (20 szt.)', 'Awokado, tofu, ogórek, tykwa, mango', 64, { e: sushiE }],
        ['Zestaw pieczony (24 szt.)', 'Rolki w tempurze i zapiekane pod sosem', 89, { e: sushiE }],
        ['Zestaw dla dwojga (40 szt.)', 'Do tego dwie zupy miso', 139, { pop: true, e: sushiE }]
      ]],
      ['Futomaki (6 szt.)', [
        ['Z łososiem i awokado', '', 32], ['Z krewetką w tempurze', '', 36], ['Wege z tofu', '', 27]
      ]],
      ['Hosomaki (8 szt.)', [['Z ogórkiem', '', 14], ['Z łososiem', '', 19], ['Z tuńczykiem', '', 22]]],
      ['Nigiri (2 szt.)', [['Łosoś', '', 16], ['Tuńczyk', '', 19], ['Krewetka', '', 17]]],
      ['Przystawki', [
        ['Zupa miso', 'Z tofu i wakame', 14], ['Edamame', 'Z solą morską', 16],
        ['Sałatka wakame', '', 17], ['Gyoza z kurczakiem (5 szt.)', '', 23]
      ]],
      ['Napoje', [['Zielona herbata mrożona', '', 11], ['Woda 0,5 l', '', 6]]]
    ]),

    lokal('pierogarnia-zosia', 'Pierogarnia Zosia', {
      kitchen: 'Polska, pierogi, zupy', cuisines: ['polska', 'obiady'], art: 'pierogi', color: '#3F6FB5',
      rating: 4.9, reviews: 2045, timeMin: 30, timeMax: 45, fee: 4.99, minOrder: 30,
      address: 'ul. Nowogrodzka 18, Warszawa'
    }, [
      ['Pierogi (10 szt.)', [
        ['Ruskie', 'Ziemniaki, twaróg, cebulka', 27, { pop: true, v: pierogiV, e: pierogiE }],
        ['Z mięsem', 'Wieprzowo-wołowe, z majerankiem', 29, { pop: true, v: pierogiV, e: pierogiE }],
        ['Z kapustą i grzybami', '', 28, { v: pierogiV, e: pierogiE }],
        ['Ze szpinakiem i fetą', '', 29, { v: pierogiV, e: pierogiE }],
        ['Z kaczką', 'Z żurawiną', 34, { v: pierogiV, e: pierogiE }]
      ]],
      ['Pierogi na słodko (10 szt.)', [
        ['Z serem', 'Ze śmietaną i cukrem', 26], ['Z jagodami', '', 29, { pop: true }], ['Z truskawkami', '', 28]
      ]],
      ['Zupy', [
        ['Żurek z jajkiem i kiełbasą', '', 19, { pop: true }], ['Rosół z makaronem', '', 15],
        ['Barszcz czerwony z uszkami', '', 18], ['Pomidorowa', 'Z ryżem albo makaronem', 15, { v: [['Z ryżem', 0], ['Z makaronem', 0]] }]
      ]],
      ['Dania domowe', [
        ['Placki ziemniaczane (4 szt.)', 'Ze śmietaną', 24], ['Gołąbki w sosie pomidorowym (2 szt.)', '', 29],
        ['Kopytka z sosem grzybowym', '', 27]
      ]],
      ['Napoje', [['Kompot 0,4 l', '', 7], ['Maślanka', '', 6]]]
    ]),

    lokal('kumo-ramen', 'Kumo Ramen', {
      kitchen: 'Ramen, japońska, azjatycka', cuisines: ['azjatycka'], art: 'ramen', color: '#D9503A',
      rating: 4.7, reviews: 742, timeMin: 35, timeMax: 50, fee: 6.99, minOrder: 45, isNew: true,
      address: 'ul. Żurawia 6, Warszawa'
    }, [
      ['Ramen', [
        ['Shoyu', 'Bulion drobiowo-sojowy, chashu, jajko, nori, szczypior', 39, { pop: true, e: ramenE }],
        ['Tonkotsu', 'Kremowy bulion wieprzowy, chashu, jajko, grzyby mun', 44, { pop: true, e: ramenE }],
        ['Miso spicy', 'Bulion miso, mielona wieprzowina, kukurydza, chili', 43, { e: ramenE }],
        ['Tantanmen', 'Sezamowy, pikantny, z mieloną wieprzowiną i pak choi', 45, { e: ramenE }],
        ['Wege shiitake', 'Bulion grzybowy, tofu, shiitake, pak choi', 39, { e: ramenE }]
      ]],
      ['Przystawki', [
        ['Gyoza wieprzowe (5 szt.)', '', 22, { pop: true }], ['Karaage', 'Chrupiący kurczak z majonezem yuzu', 26],
        ['Kimchi', '', 12], ['Bao z boczkiem (2 szt.)', '', 27]
      ]],
      ['Donburi', [['Chashu don', 'Ryż, wieprzowina, jajko, marynowany imbir', 32], ['Karaage don', '', 31]]],
      ['Napoje', [['Lemoniada yuzu', '', 13], ['Herbata jaśminowa', '', 10]]]
    ]),

    lokal('dom-curry', 'Dom Curry', {
      kitchen: 'Indyjska, wegetariańska', cuisines: ['indyjska', 'zdrowe'], art: 'curry', color: '#7B2D5B',
      rating: 4.6, reviews: 1120, timeMin: 35, timeMax: 55, fee: 5.99, minOrder: 45,
      badge: 'Naan gratis od 80 zł', address: 'ul. Krucza 23, Warszawa'
    }, [
      ['Curry', [
        ['Butter chicken', 'Kurczak w maślano-pomidorowym sosie', 42, { pop: true, v: curryV, e: curryE }],
        ['Chicken tikka masala', 'Kurczak z pieca tandoor w sosie masala', 42, { pop: true, v: curryV, e: curryE }],
        ['Palak paneer', 'Ser paneer w sosie szpinakowym', 38, { v: curryV, e: curryE }],
        ['Chana masala', 'Ciecierzyca w pomidorach, wegańskie', 34, { v: curryV, e: curryE }],
        ['Lamb rogan josh', 'Jagnięcina duszona w aromatycznym sosie', 49, { v: curryV, e: curryE }],
        ['Dal makhani', 'Czarna soczewica gotowana z masłem', 33, { v: curryV, e: curryE }]
      ]],
      ['Przystawki', [
        ['Samosa warzywna (2 szt.)', '', 16, { pop: true }], ['Pakora z cebuli', '', 17], ['Papadam z sosami', '', 12]
      ]],
      ['Biryani', [['Biryani z kurczakiem', '', 39, { v: curryV }], ['Biryani warzywne', '', 35, { v: curryV }]]],
      ['Desery i napoje', [['Mango lassi', '', 13], ['Gulab jamun (2 szt.)', '', 14], ['Masala chai', '', 10]]]
    ]),

    lokal('zielona-miska', 'Zielona Miska', {
      kitchen: 'Bowle, sałatki, zdrowe', cuisines: ['zdrowe'], art: 'salatka', color: '#CFE3B4',
      rating: 4.5, reviews: 534, timeMin: 25, timeMax: 40, fee: 0, minOrder: 35,
      badge: 'Darmowa dostawa', address: 'ul. Mokotowska 50, Warszawa'
    }, [
      ['Bowle', [
        ['Bowl z łososiem', 'Łosoś, awokado, edamame, mango, sezam', 41, { pop: true, v: bowlV }],
        ['Bowl z kurczakiem teriyaki', 'Kurczak, brokuł, marchew, ogórek, sos teriyaki', 37, { pop: true, v: bowlV }],
        ['Bowl z tofu', 'Marynowane tofu, kimchi, edamame, rzodkiewka', 35, { v: bowlV }],
        ['Bowl z halloumi', 'Halloumi, pieczony batat, ciecierzyca, hummus', 37, { v: bowlV }]
      ]],
      ['Sałatki', [
        ['Cezar z kurczakiem', '', 33, { pop: true }], ['Grecka', '', 29], ['Z kozim serem i burakiem', 'Z orzechami i miodem', 34]
      ]],
      ['Wrapy', [['Z falafelem i hummusem', '', 28], ['Z kurczakiem i warzywami', '', 29]]],
      ['Zupy krem', [['Z pomidorów', '', 16], ['Z dyni', 'Z mlekiem kokosowym', 17]]],
      ['Soki i smoothie', [['Smoothie zielone', 'Szpinak, banan, mango', 16], ['Sok pomarańczowy wyciskany', '', 15], ['Kombucha', '', 14]]]
    ]),

    lokal('slodki-zwitek', 'Słodki Zwitek', {
      kitchen: 'Naleśniki, gofry, desery', cuisines: ['desery'], art: 'nalesniki', color: '#F6C7D0',
      rating: 4.8, reviews: 1388, timeMin: 20, timeMax: 35, fee: 3.99, minOrder: 25,
      address: 'ul. Chmielna 9, Warszawa'
    }, [
      ['Naleśniki na słodko', [
        ['Z serem i rodzynkami', '', 22, { pop: true }], ['Z czekoladą i bananem', '', 24, { pop: true }],
        ['Z jabłkami i cynamonem', '', 23], ['Z mascarpone i malinami', '', 27]
      ]],
      ['Naleśniki wytrawne', [
        ['Ze szpinakiem i fetą', '', 26], ['Z kurczakiem i pieczarkami', 'Zapiekane z serem', 28], ['Z szynką i serem', '', 26]
      ]],
      ['Pancakes', [
        ['Z syropem klonowym i masłem', '', 25, { pop: true }], ['Z owocami leśnymi', 'I bitą śmietaną', 28]
      ]],
      ['Gofry', [['Z bitą śmietaną', '', 17], ['Z owocami', '', 21]]],
      ['Napoje', [['Kawa latte', '', 13], ['Gorąca czekolada', '', 14], ['Lemoniada', '', 11]]]
    ]),

    lokal('makaron-i-spolka', 'Makaron i Spółka', {
      kitchen: 'Włoska, makarony, risotto', cuisines: ['wloska'], art: 'makaron', color: '#A63A2A',
      rating: 4.4, reviews: 876, timeMin: 30, timeMax: 50, fee: 5.99, minOrder: 40,
      open: false, opensAt: '16:00', address: 'ul. Koszykowa 30, Warszawa'
    }, [
      ['Makarony', [
        ['Carbonara', 'Guanciale, żółtka, pecorino', 36, { pop: true }], ['Bolognese', 'Ragù gotowane 6 godzin', 35, { pop: true }],
        ['Pesto genovese', '', 33], ['Frutti di mare', 'Krewetki, mule, kalmary', 46], ['Lasagne', '', 37],
        ['Gnocchi quattro formaggi', '', 36]
      ]],
      ['Risotto', [['Z grzybami leśnymi', '', 38], ['Z krewetkami', '', 45]]],
      ['Przystawki', [['Arancini (3 szt.)', '', 22], ['Burrata z pomidorami', '', 34]]],
      ['Desery', [['Cannoli (2 szt.)', '', 19], ['Tiramisu', '', 21]]]
    ]),

    lokal('kukurydza-taqueria', 'Kukurydza Taqueria', {
      kitchen: 'Meksykańska, tacos, burrito', cuisines: ['meksykanska'], art: 'tacos', color: '#1F8A8A',
      rating: 4.6, reviews: 431, timeMin: 30, timeMax: 45, fee: 5.49, minOrder: 35,
      address: 'ul. Oleandrów 4, Warszawa'
    }, [
      ['Tacos (3 szt.)', [
        ['Al pastor', 'Wieprzowina, ananas, kolendra, cebula', 32, { pop: true, e: tacoE }],
        ['Z szarpaną wołowiną', '', 34, { pop: true, e: tacoE }],
        ['Z kurczakiem tinga', '', 31, { e: tacoE }], ['Z kalafiorem', 'Wegańskie', 29, { e: tacoE }]
      ]],
      ['Burrito', [
        ['Z wołowiną', '', 35, { pop: true, v: burritoV, e: tacoE }], ['Z kurczakiem', '', 33, { v: burritoV, e: tacoE }],
        ['Wege z czarną fasolą', '', 31, { v: burritoV, e: tacoE }]
      ]],
      ['Quesadilla', [['Z serem', '', 26], ['Z kurczakiem', '', 31]]],
      ['Dodatki', [['Nachos z guacamole', '', 24], ['Salsa i chipsy', '', 15]]],
      ['Napoje', [['Agua fresca arbuzowa', '', 12], ['Lemoniada limonkowa', '', 11]]]
    ]),

    lokal('bar-pod-zegarem', 'Bar Pod Zegarem', {
      kitchen: 'Obiady domowe, polska', cuisines: ['obiady', 'polska'], art: 'obiad', color: '#E7DCC3',
      rating: 4.3, reviews: 1905, timeMin: 25, timeMax: 40, fee: 3.49, minOrder: 25,
      badge: 'Zestaw dnia 26 zł', address: 'ul. Piękna 20, Warszawa'
    }, [
      ['Zestawy obiadowe', [
        ['Schabowy z ziemniakami i mizerią', '', 32, { pop: true }], ['Kotlet mielony z buraczkami', '', 28, { pop: true }],
        ['De volaille z frytkami', '', 34], ['Filet z dorsza z surówką', '', 36],
        ['Zestaw dnia', 'Zupa i drugie danie, pytaj o dzisiejsze', 26, { pop: true }]
      ]],
      ['Zupy', [['Pomidorowa z ryżem', '', 12], ['Ogórkowa', '', 12], ['Rosół', '', 13], ['Flaki', '', 17]]],
      ['Dania mączne', [['Naleśniki z serem (3 szt.)', '', 19], ['Leniwe z bułką tartą', '', 20], ['Pyzy z mięsem', '', 24]]],
      ['Surówki i dodatki', [['Mizeria', '', 7], ['Buraczki', '', 7], ['Kapusta zasmażana', '', 8], ['Ziemniaki z koperkiem', '', 7]]],
      ['Napoje', [['Kompot', '', 6], ['Woda 0,5 l', '', 4]]]
    ])
  ];

  window.SZAMKA_START = {
    seed: 'start-1',
    settings: {
      heroTitle: 'Na co masz dziś ochotę?',
      heroSub: 'Wpisz adres, a pokażemy lokale, które dowożą pod Twoje drzwi.',
      promoBar: 'Pierwsze zamówienie? Wpisz kod SZAMKA i dostawa jest za darmo.',
      serviceFee: 1.99,
      pin: '1234',
      cuisines: [
        { id: 'pizza', name: 'Pizza', art: 'pizza' },
        { id: 'burgery', name: 'Burgery', art: 'burger' },
        { id: 'kebab', name: 'Kebab', art: 'kebab' },
        { id: 'sushi', name: 'Sushi', art: 'sushi' },
        { id: 'polska', name: 'Polska', art: 'pierogi' },
        { id: 'azjatycka', name: 'Azjatycka', art: 'ramen' },
        { id: 'indyjska', name: 'Indyjska', art: 'curry' },
        { id: 'wloska', name: 'Włoska', art: 'makaron' },
        { id: 'zdrowe', name: 'Zdrowe', art: 'salatka' },
        { id: 'desery', name: 'Desery', art: 'nalesniki' },
        { id: 'meksykanska', name: 'Meksykańska', art: 'tacos' },
        { id: 'obiady', name: 'Obiady domowe', art: 'obiad' }
      ],
      vouchers: [
        { code: 'SZAMKA', kind: 'dostawa', value: 0 },
        { code: 'GLODNY10', kind: 'kwota', value: 10 }
      ],
      couriers: ['Kamil', 'Oskar', 'Wiktoria', 'Mateusz', 'Ola', 'Dawid'],
      reveal: { on: true, title: 'To był żart!', text: 'Nic do Ciebie nie jedzie. Możesz odetchnąć.' }
    },
    user: { address: '', apt: '', floor: '', name: '', phone: '', email: '' },
    restaurants: restaurants,
    orders: []
  };
})();
