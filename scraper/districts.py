# -*- coding: utf-8 -*-
"""
İlçe → il eşlemesi (plaka kodu ile).

Yalnızca başka bir ilde de bulunan (Gölbaşı, Kale, Yenişehir, Kemalpaşa, Ereğli...)
ya da gündelik sözcükle karışmayan ilçe adları alınmıştır. Eksik bir ilçe için ilgili
satıra adını eklemek yeterlidir.
"""

_RAW = """
01: Seyhan, Çukurova, Sarıçam, Yüreğir, Ceyhan, Kozan, İmamoğlu, Karataş, Pozantı, Aladağ, Feke, Saimbeyli, Tufanbeyli, Yumurtalık
02: Kahta, Besni, Gerger, Samsat, Çelikhan
03: Sandıklı, Bolvadin, Dinar, Emirdağ, Sultandağı, Şuhut, İscehisar
04: Doğubayazıt, Patnos, Diyadin, Taşlıçay, Eleşkirt, Tutak
05: Merzifon, Suluova, Taşova, Göynücek, Hamamözü, Gümüşhacıköy
06: Çankaya, Keçiören, Yenimahalle, Mamak, Etimesgut, Sincan, Altındağ, Pursaklar, Polatlı, Beypazarı, Kahramankazan, Kızılcahamam, Elmadağ, Çubuk, Haymana, Nallıhan, Akyurt, Ayaş, Güdül, Kalecik, Şereflikoçhisar, Çamlıdere
07: Muratpaşa, Kepez, Konyaaltı, Döşemealtı, Alanya, Manavgat, Serik, Kumluca, Finike, Elmalı, Korkuteli, Gazipaşa, Demre, İbradı, Gündoğmuş, Akseki
08: Hopa, Arhavi, Borçka, Şavşat, Yusufeli, Ardanuç, Murgul
09: Efeler, Nazilli, Söke, Kuşadası, Didim, Germencik, Çine, İncirliova, Koçarlı, Sultanhisar, Kuyucak, Karacasu, Bozdoğan, Karpuzlu
10: Altıeylül, Karesi, Edremit, Bandırma, Ayvalık, Burhaniye, Gönen, Susurluk, Bigadiç, Dursunbey, Erdek, Havran, Sındırgı, Kepsut, Savaştepe, Manyas, Gömeç, İvrindi
11: Bozüyük, Osmaneli, Söğüt, Gölpazarı, Pazaryeri
12: Solhan, Karlıova
13: Tatvan, Ahlat, Adilcevaz, Hizan, Mutki, Güroymak
14: Mudurnu, Gerede, Göynük, Mengen, Yeniçağa, Dörtdivan, Kıbrıscık
15: Bucak, Gölhisar, Yeşilova, Tefenni, Ağlasun, Çavdır
16: Osmangazi, Nilüfer, Yıldırım, Mudanya, Gemlik, İnegöl, Mustafakemalpaşa, Orhangazi, Karacabey, Kestel, Gürsu, Orhaneli, Büyükorhan, Harmancık, İznik
17: Biga, Gelibolu, Ayvacık, Bayramiç, Ezine, Lapseki, Eceabat, Gökçeada, Bozcaada
18: Ilgaz, Çerkeş, Şabanözü, Kurşunlu, Eldivan
19: Sungurlu, Osmancık, İskilip, Mecitözü, Uğurludağ, Boğazkale
20: Pamukkale, Merkezefendi, Çivril, Acıpayam, Tavas, Sarayköy, Buldan, Honaz, Çameli, Serinhisar
21: Bağlar, Kayapınar, Bismil, Ergani, Silvan, Çermik, Kulp, Lice
22: Keşan, Uzunköprü, Havsa, İpsala, Enez, Lalapaşa, Süloğlu
23: Karakoçan, Kovancılar, Sivrice, Baskil, Arıcak, Keban
24: Üzümlü, Refahiye, Tercan, Çayırlı, Kemaliye, Otlukbeli
25: Yakutiye, Palandöken, Aziziye, Horasan, Oltu, Pasinler, Tortum, Hınıs, Narman, İspir, Şenkaya, Tekman, Aşkale
26: Odunpazarı, Tepebaşı, Sivrihisar, Çifteler, Seyitgazi, Mihalıççık, Sarıcakaya, Günyüzü, Mahmudiye, Beylikova, Mihalgazi
27: Şahinbey, Şehitkamil, Nizip, İslahiye, Nurdağı, Araban, Oğuzeli, Yavuzeli, Karkamış
28: Bulancak, Espiye, Tirebolu, Görele, Eynesil, Keşap, Şebinkarahisar, Alucra, Piraziz, Yağlıdere
29: Kelkit, Şiran, Torul, Kürtün
30: Yüksekova, Şemdinli, Çukurca
31: Antakya, İskenderun, Defne, Arsuz, Dörtyol, Kırıkhan, Reyhanlı, Samandağ, Altınözü, Hassa, Payas, Erzin, Yayladağı
32: Eğirdir, Yalvaç, Şarkikaraağaç, Gelendost, Atabey, Sütçüler, Senirkent, Uluborlu, Keçiborlu
33: Mezitli, Toroslar, Tarsus, Erdemli, Silifke, Anamur, Gülnar, Bozyazı, Çamlıyayla
34: Kadıköy, Üsküdar, Ataşehir, Maltepe, Kartal, Pendik, Tuzla, Sultanbeyli, Sancaktepe, Çekmeköy, Ümraniye, Beykoz, Sarıyer, Beyoğlu, Şişli, Kağıthane, Bakırköy, Zeytinburnu, Bayrampaşa, Esenler, Bağcılar, Güngören, Küçükçekmece, Avcılar, Esenyurt, Beylikdüzü, Büyükçekmece, Çatalca, Silivri, Arnavutköy, Başakşehir, Sultangazi, Gaziosmanpaşa, Eyüpsultan, Bahçelievler, Adalar
35: Bornova, Karşıyaka, Buca, Bayraklı, Çiğli, Gaziemir, Balçova, Narlıdere, Karabağlar, Güzelbahçe, Urla, Çeşme, Karaburun, Seferihisar, Torbalı, Bergama, Dikili, Aliağa, Foça, Menemen, Ödemiş, Bayındır, Kiraz, Beydağ, Selçuk, Kınık
36: Sarıkamış, Kağızman, Arpaçay, Digor, Susuz, Akyaka
37: Tosya, Taşköprü, İnebolu, Daday, Devrekani, Cide, Küre, Azdavay, Abana, Çatalzeytin, Doğanyurt, İhsangazi, Şenpazar, Seydiler
38: Melikgazi, Kocasinan, Talas, Develi, Yahyalı, Bünyan, İncesu, Tomarza, Sarıoğlan, Sarız, Hacılar, Özvatan, Akkışla, Felahiye, Yeşilhisar
39: Lüleburgaz, Babaeski, Vize, Pınarhisar, Demirköy, Kofçaz, Pehlivanköy
40: Kaman, Mucur, Çiçekdağı, Boztepe, Akçakent
41: İzmit, Gebze, Darıca, Körfez, Gölcük, Karamürsel, Kandıra, Derince, Dilovası, Çayırova, Başiskele, Kartepe
42: Selçuklu, Karatay, Meram, Akşehir, Beyşehir, Seydişehir, Cihanbeyli, Çumra, Karapınar, Bozkır, Doğanhisar, Sarayönü, Kadınhanı, Altınekin
43: Tavşanlı, Simav, Gediz, Altıntaş, Domaniç, Hisarcık, Aslanapa, Dumlupınar, Pazarlar, Şaphane
44: Battalgazi, Yeşilyurt, Doğanşehir, Akçadağ, Darende, Hekimhan, Arapgir, Pütürge, Yazıhan, Arguvan, Kuluncak, Doğanyol
45: Yunusemre, Şehzadeler, Akhisar, Turgutlu, Salihli, Alaşehir, Saruhanlı, Kırkağaç, Demirci, Gördes, Sarıgöl, Ahmetli, Selendi, Gölmarmara
46: Dulkadiroğlu, Onikişubat, Elbistan, Afşin, Pazarcık, Türkoğlu, Göksun, Andırın, Çağlayancerit, Ekinözü, Nurhak
47: Artuklu, Kızıltepe, Midyat, Nusaybin, Derik, Mazıdağı, Savur, Dargeçit, Ömerli, Yeşilli
48: Menteşe, Bodrum, Marmaris, Fethiye, Milas, Datça, Ortaca, Dalaman, Köyceğiz, Yatağan, Kavaklıdere, Seydikemer
49: Malazgirt, Bulanık, Varto, Korkut
50: Ürgüp, Avanos, Gülşehir, Derinkuyu, Kozaklı, Acıgöl, Hacıbektaş
51: Ulukışla, Çiftlik, Altunhisar, Çamardı
52: Altınordu, Ünye, Fatsa, Gülyalı, Gölköy, Korgan, Kumru, Mesudiye, Aybastı, Çaybaşı, Çatalpınar, Çamaş, İkizce, Kabadüz, Kabataş, Gürgentepe
53: Ardeşen, Çayeli, Fındıklı, Kalkandere, Güneysu, Derepazarı, Hemşin, İkizdere, İyidere, Çamlıhemşin
54: Adapazarı, Serdivan, Erenler, Arifiye, Akyazı, Karasu, Kocaali, Sapanca, Geyve, Pamukova, Taraklı, Ferizli, Karapürçek, Söğütlü, Kaynarca
55: İlkadım, Atakum, Canik, Tekkeköy, Bafra, Çarşamba, Vezirköprü, Havza, Alaçam, Ladik, Salıpazarı, Asarcık, Yakakent
56: Kurtalan, Baykan, Pervari, Şirvan, Eruh
57: Ayancık, Boyabat, Gerze, Durağan, Erfelek, Türkeli, Saraydüzü
58: Şarkışla, Suşehri, Divriği, Gemerek, Yıldızeli, Hafik, Kangal, Gürün, Koyulhisar, Akıncılar, Doğanşar, İmranlı, Gölova
59: Süleymanpaşa, Çorlu, Çerkezköy, Ergene, Kapaklı, Malkara, Hayrabolu, Muratlı, Şarköy, Marmaraereğlisi
60: Erbaa, Niksar, Turhal, Zile, Reşadiye, Almus, Artova, Sulusaray, Başçiftlik
61: Ortahisar, Akçaabat, Araklı, Sürmene, Vakfıkebir, Yomra, Arsin, Beşikdüzü, Çarşıbaşı, Çaykara, Maçka, Şalpazarı, Tonya, Dernekpazarı
62: Ovacık, Pülümür, Hozat, Çemişgezek, Mazgirt, Nazımiye, Pertek
63: Haliliye, Eyyübiye, Karaköprü, Siverek, Viranşehir, Birecik, Suruç, Akçakale, Ceylanpınar, Halfeti, Hilvan, Bozova, Harran
64: Banaz, Eşme, Sivaslı, Karahallı
65: Tuşba, İpekyolu, Erciş, Gevaş, Çaldıran, Muradiye, Özalp, Başkale, Gürpınar, Bahçesaray
66: Sorgun, Akdağmadeni, Boğazlıyan, Çayıralan, Çekerek, Şefaatli, Yerköy, Kadışehri, Saraykent
67: Çaycuma, Devrek, Alaplı, Gökçebey, Kilimli, Kozlu
68: Eskil, Gülağaç, Sarıyahşi, Sultanhanı, Ağaçören
69: Aydıntepe, Demirözü
70: Ermenek, Kazımkarabekir, Ayrancı, Başyayla, Sarıveliler
71: Yahşihan, Keskin, Bahşılı, Balışeyh, Karakeçili, Sulakyurt
72: Kozluk, Sason, Beşiri, Gercüş, Hasankeyf
73: Cizre, Silopi, İdil, Uludere, Beytüşşebap, Güçlükonak
74: Amasra, Kurucaşile
75: Çıldır, Damal, Posof, Hanak
76: Tuzluca, Karakoyunlu
77: Çınarcık, Armutlu, Altınova, Çiftlikköy
78: Safranbolu, Eskipazar, Eflani
79: Elbeyli, Musabeyli, Polateli
80: Kadirli, Düziçi, Toprakkale, Hasanbeyli, Sumbas
81: Akçakoca, Kaynaşlı, Gölyaka, Cumayeri, Çilimli, Yığılca, Gümüşova
"""

# Gündelik sözcük ya da kişi adıyla karışabilenler: yalnızca metinde "belediye"
# (ya da kaymakamlık/ilçe) geçiyorsa ilçe sayılır.
_RISKY_RAW = """
34: Fatih, Beşiktaş, Şile
35: Konak, Menderes, Tire
55: Terme
52: Perşembe
45: Soma
10: Hendek
54: Hendek
"""


def _parse(raw):
    out = []
    for line in raw.strip().splitlines():
        plaka, names = line.split(":", 1)
        for n in names.split(","):
            n = n.strip()
            if n:
                out.append((plaka.strip(), n))
    return out


DISTRICTS = _parse(_RAW)          # [(plaka, ilçe adı), ...]
RISKY_DISTRICTS = _parse(_RISKY_RAW)

# İlçe olmayan ama ili belirten kurum kısaltmaları
ALIASES = [("34", "İBB"), ("06", "ABB"), ("35", "İzBB")]
