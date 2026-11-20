# -*- coding: utf-8 -*-
"""Erzeugt data/zhenghe.json: die sieben Flottenfahrten des Zheng He (1405–1433).

Format wie data/handel.json (verbindungen, orte, waren) plus Ereignisse und Infotext.
Die Seewege werden aus Teilstrecken (LEGS) zusammengesetzt, damit gleiche Abschnitte
bei allen Fahrten gleich verlaufen. Alle Verläufe sind schematisch.

Stationen nach: Ma Huan, Yingya Shenglan (1451); Fei Xin, Xingcha Shenglan (1436);
Mingshi 304; Inschriften von Liujiagang und Changle (1431); E. L. Dreyer, Zheng He (2007).
Nur gesicherte Stationen; Unsicheres ist als „umstritten“ markiert.
Die Amerika-/Weltumsegelungsthese (G. Menzies, „1421“) ist widerlegt und wird NICHT dargestellt.

Aufruf (im Projektordner):  python build_zhenghe.py
Optional mit shapely: prüft, ob ein Seeweg über Land führt.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- Teilstrecken [lng, lat] ----------------
LEGS = {
    'nanjing-liujiagang': [[118.73, 32.07], [119.4, 32.25], [120.3, 31.95], [121.27, 31.6]],
    'liujiagang-changle': [[121.27, 31.6], [121.9, 31.25], [122.4, 30.6], [122.3, 29.6], [121.8, 28.4], [120.9, 27.2], [120.1, 26.4], [119.62, 25.98]],
    'changle-champa': [[119.62, 25.98], [119.8, 25.3], [118.9, 24.3], [117.5, 23.0], [115.5, 22.0], [113.5, 20.8], [112.0, 19.0], [111.0, 17.2], [109.8, 15.0], [109.3, 13.77]],
    'changle-quanzhou': [[119.62, 25.98], [119.8, 25.3], [118.59, 24.87]],
    'quanzhou-champa': [[118.59, 24.87], [118.9, 24.3], [117.5, 23.0], [115.5, 22.0], [113.5, 20.8], [112.0, 19.0], [111.0, 17.2], [109.8, 15.0], [109.3, 13.77]],
    'champa-camau': [[109.3, 13.77], [109.6, 12.0], [109.1, 10.5], [107.5, 9.2], [106.0, 8.0]],
    'camau-java': [[106.0, 8.0], [106.5, 5.0], [107.0, 1.5], [108.2, -1.8], [109.5, -4.5], [111.5, -5.8], [112.5, -6.6], [112.73, -7.15]],
    'camau-malakka': [[106.0, 8.0], [105.5, 5.0], [104.6, 2.2], [104.3, 1.3], [103.6, 1.15], [102.9, 1.7], [102.25, 2.15]],
    'java-palembang': [[112.73, -7.15], [112.5, -6.6], [110.0, -5.5], [107.6, -4.0], [107.2, -2.6], [106.5, -1.0], [105.6, -1.2], [105.0, -1.8], [104.76, -2.99]],
    'java-malakka': [[112.73, -7.15], [112.5, -6.6], [110.0, -5.5], [107.6, -4.0], [107.2, -2.6], [106.5, -1.0], [105.5, 0.3], [104.4, 1.2], [103.6, 1.15], [102.9, 1.7], [102.25, 2.15]],
    'palembang-malakka': [[104.76, -2.99], [105.0, -1.8], [105.3, -1.0], [105.5, 0.3], [104.4, 1.2], [103.6, 1.15], [102.9, 1.7], [102.25, 2.15]],
    'malakka-semudera': [[102.25, 2.15], [101.2, 2.6], [100.3, 3.4], [99.2, 4.4], [98.2, 5.2], [97.15, 5.25]],
    'semudera-galle': [[97.15, 5.25], [95.6, 6.0], [92.0, 6.3], [86.0, 5.9], [81.5, 5.6], [80.22, 5.98]],
    'galle-beruwala': [[80.22, 5.98], [79.95, 6.48]],
    'galle-komorin': [[80.22, 5.98], [79.5, 6.6], [78.0, 7.6], [77.3, 7.9]],
    'beruwala-komorin': [[79.95, 6.48], [79.4, 7.0], [78.0, 7.6], [77.3, 7.9]],
    'komorin-quilon': [[77.3, 7.9], [76.55, 8.85]],
    'quilon-cochin': [[76.55, 8.85], [76.15, 9.97]],
    'komorin-cochin': [[77.3, 7.9], [76.4, 8.9], [76.15, 9.97]],
    'cochin-calicut': [[76.15, 9.97], [75.6, 11.0], [75.73, 11.25]],
    'komorin-calicut': [[77.3, 7.9], [76.4, 8.9], [75.9, 10.0], [75.5, 11.0], [75.73, 11.25]],
    'calicut-hormuz': [[75.73, 11.25], [74.0, 13.5], [69.5, 18.5], [64.0, 22.0], [60.8, 23.3], [58.4, 24.9], [57.6, 25.5], [57.2, 25.9], [56.9, 26.2], [56.6, 26.7], [56.46, 27.05]],
    'hormuz-aden': [[56.46, 27.05], [56.6, 26.7], [56.9, 26.2], [57.2, 25.9], [57.6, 25.5], [58.4, 24.9], [59.3, 23.6], [60.3, 22.4], [59.6, 20.3], [57.8, 18.2], [55.5, 17.0], [54.1, 16.85], [52.0, 15.5], [49.5, 14.0], [47.0, 13.0], [45.03, 12.75]],
    'aden-mogadischu': [[45.03, 12.75], [46.5, 12.3], [49.5, 12.0], [50.5, 12.2], [51.4, 12.2], [51.6, 11.9], [51.7, 10.5], [50.3, 7.0], [48.6, 4.5], [46.6, 2.6], [45.35, 2.04]],
    'mogadischu-brava': [[45.35, 2.04], [44.03, 1.11]],
    'brava-malindi': [[44.03, 1.11], [42.8, -0.5], [41.9, -1.5], [41.2, -2.0], [40.9, -2.5], [40.6, -2.6], [40.12, -3.22]],
    # Abzweige (Teilflotten)
    'camau-siam': [[106.0, 8.0], [104.9, 8.3], [104.5, 9.0], [101.8, 11.6], [101.3, 12.3], [100.9, 12.6], [100.75, 12.9], [100.58, 13.5], [100.57, 14.35]],
    'calicut-male': [[75.73, 11.25], [74.5, 8.0], [73.51, 4.18]],
    'male-mogadischu': [[73.51, 4.18], [65.0, 3.6], [55.0, 3.0], [48.0, 2.4], [45.35, 2.04]],
    'calicut-dhofar': [[75.73, 11.25], [70.0, 14.0], [62.0, 16.0], [56.0, 16.5], [54.1, 16.85]],
    'dhofar-aden': [[54.1, 16.85], [52.0, 15.5], [49.5, 14.0], [47.0, 13.0], [45.03, 12.75]],
    'semudera-bengalen': [[97.15, 5.25], [95.6, 6.0], [93.5, 6.3], [92.5, 7.0], [92.0, 8.0], [91.8, 12.0], [91.5, 17.5], [91.4, 21.0], [91.8, 22.33]],
    'calicut-dschidda': [[75.73, 11.25], [70.0, 13.0], [60.0, 13.5], [52.0, 13.6], [47.0, 12.9], [44.0, 12.4], [43.35, 12.6], [42.6, 14.0], [41.0, 17.0], [39.8, 19.8], [39.17, 21.48]],
}


def join(*names):
    out = []
    for n in names:
        p = LEGS[n]
        out.extend(p if not out else p[1:])
    return out


START = ['nanjing-liujiagang', 'liujiagang-changle']

# ---------------- Häfen ----------------
# funktion: kurze Rolle; besuche: Fahrten (Nummern), an denen der Hafen belegt angelaufen wurde
ORTE = [
    dict(id='nanjing', name='Nanjing', lng=118.73, lat=32.07, fahrten=[1, 2, 3, 4, 5, 6, 7], funktion='Hauptstadt bis 1421, Werft (Longwan), Start und Ziel der Flotte', belegt='belegt',
         quelle='Mingshi 304; Dreyer 2007', hinweis='Hier wurden viele Schiffe gebaut. Am Ende jeder Fahrt kamen die Gesandten fremder Herrscher an den Kaiserhof.'),
    dict(id='liujiagang', name='Liujiagang (Taicang)', lng=121.27, lat=31.6, fahrten=[1, 2, 3, 4, 5, 6, 7], funktion='Sammelplatz an der Jangtse-Mündung', belegt='belegt',
         quelle='Liujiagang-Inschrift (1431)', hinweis='Vor der Fahrt aufs offene Meer sammelte sich die Flotte hier. 1431 ließ Zheng He eine Inschrift über alle Fahrten aufstellen.'),
    dict(id='changle', name='Changle (Fujian)', lng=119.62, lat=25.98, fahrten=[1, 2, 3, 4, 5, 6, 7], funktion='Sammelhafen: Warten auf den Nordost-Monsun', belegt='belegt',
         quelle='Changle-Inschrift (1431/32)', hinweis='Am Ankerplatz Taiping wartete die Flotte oft wochenlang auf günstige Winde.'),
    dict(id='quanzhou', name='Quanzhou', lng=118.59, lat=24.87, fahrten=[5], funktion='Hafen in Fujian, Station der 5. Fahrt', belegt='belegt',
         quelle='Inschrift am Grab der Heiligen (Lingshan), Quanzhou, 1417', hinweis='Eine Inschrift von 1417 erwähnt Zheng Hes Besuch vor der Abfahrt.'),
    dict(id='champa', name='Champa (Vijaya)', lng=109.3, lat=13.77, fahrten=[1, 2, 3, 4, 5, 7], funktion='Erste Station im Süden, Tributstaat', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan', hinweis='Heute Mittelvietnam (bei Quy Nhon).'),
    dict(id='siam', name='Siam (Ayutthaya)', lng=100.57, lat=14.35, fahrten=[2], funktion='Tributmission (Teilflotte)', belegt='belegt',
         quelle='Dreyer 2007; Fei Xin', hinweis='Wahrscheinlich besuchte nur ein Teil der Flotte Siam. Ob auf der 6. Fahrt erneut, ist unklar.'),
    dict(id='java', name='Java (Nordküste, Surabaya)', lng=112.73, lat=-7.15, fahrten=[1, 2, 3, 4, 5, 7], funktion='Handels- und Tributstation (Reich Majapahit)', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan', hinweis='Die Flotte ankerte an mehreren Orten der Nordküste (z. B. Tuban, Gresik, Surabaya). Für die 7. Fahrt ist Surabaya genannt; der Punkt steht für die ganze Nordküste. Chinesische Kupfermünzen waren hier ein übliches Zahlungsmittel.'),
    dict(id='palembang', name='Palembang', lng=104.76, lat=-2.99, fahrten=[1, 4, 5, 7], funktion='1407 Kampf gegen den Seeräuber Chen Zuyi', belegt='belegt',
         quelle='Mingshi 304; Ma Huan', hinweis='Auf der Rückfahrt 1407 besiegte die Flotte Chen Zuyi und brachte ihn nach Nanjing.'),
    dict(id='malakka', name='Malakka', lng=102.25, lat=2.15, fahrten=[1, 2, 3, 4, 5, 7], funktion='Depot und Stützpunkt (befestigtes Lager)', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan', hinweis='Die Flotte errichtete hier ein umzäuntes Lager mit Lagerhäusern. Waren wurden gesammelt, bis der Monsun die Weiterfahrt erlaubte.'),
    dict(id='semudera', name='Semudera (Nordsumatra)', lng=97.15, lat=5.25, fahrten=[1, 2, 3, 4, 5, 6, 7], funktion='Letzte Station vor der Überfahrt; 1421 Teilung der Flotte', belegt='belegt',
         quelle='Ma Huan; Dreyer 2007', hinweis='Auf der 6. Fahrt teilte sich die Flotte hier in mehrere Geschwader.'),
    dict(id='galle', name='Galle (Ceylon)', lng=80.22, lat=5.98, fahrten=[3], funktion='Landung 1410; dreisprachige Inschrift', belegt='belegt',
         quelle='Inschrift von Galle (chinesisch, tamilisch, persisch, datiert 1409); Mingshi 304', hinweis='1411 kam es auf Ceylon zum Kampf mit König Alakeshvara (bei Kotte). Zheng He nahm ihn gefangen und brachte ihn nach Nanjing. Auch andere Fahrten berührten Ceylon, der genaue Hafen ist dort aber nicht überliefert.'),
    dict(id='beruwala', name='Beruwala (Ceylon)', lng=79.95, lat=6.48, fahrten=[7], funktion='Station der 7. Fahrt', belegt='belegt',
         quelle='Zhu Yunming, Qianwenji (Reiseplan der 7. Fahrt)', hinweis=''),
    dict(id='quilon', name='Quilon (Kollam)', lng=76.55, lat=8.85, fahrten=[1, 2, 3], funktion='Handelshafen (Pfeffer)', belegt='belegt',
         quelle='Ma Huan; Dreyer 2007', hinweis=''),
    dict(id='cochin', name='Cochin', lng=76.15, lat=9.97, fahrten=[2, 3, 4, 5, 6], funktion='Handelshafen (Pfeffer)', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan', hinweis=''),
    dict(id='calicut', name='Calicut', lng=75.73, lat=11.25, fahrten=[1, 2, 3, 4, 5, 6, 7], funktion='Hauptziel in Indien, großer Pfeffermarkt', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan; Mingshi 304', hinweis='Calicut war Ziel der ersten drei Fahrten und Ausgangspunkt für die Weiterfahrt nach Arabien und Afrika.'),
    dict(id='malediven', name='Malediven', lng=73.51, lat=4.18, fahrten=[4, 5, 6], funktion='Station (Teilflotte)', belegt='belegt',
         quelle='Ma Huan („Liushan“)', hinweis='Ma Huan nennt die Inseln Liushan.'),
    dict(id='bengalen', name='Bengalen (Chittagong)', lng=91.8, lat=22.33, fahrten=[7], funktion='Tributmission (Teilflotte unter Hong Bao)', belegt='belegt',
         quelle='Ma Huan; Dreyer 2007', hinweis='1414 kam eine Giraffe als Geschenk des Herrschers von Bengalen an den Kaiserhof. Bengalische Gesandte reisten dabei mit chinesischen Schiffen.'),
    dict(id='hormuz', name='Hormuz', lng=56.46, lat=27.05, fahrten=[4, 5, 6, 7], funktion='Großer Handelsplatz am Persischen Golf', belegt='belegt',
         quelle='Ma Huan, Yingya Shenglan', hinweis='Hier gab es Edelsteine, Perlen und Waren aus Persien und Arabien.'),
    dict(id='dhofar', name='Dhofar (Zufar)', lng=54.1, lat=16.85, fahrten=[6], funktion='Weihrauchhafen (Teilflotte)', belegt='belegt',
         quelle='Ma Huan („Zufaer“); Dreyer 2007', hinweis='Hier wurde Weihrauch gehandelt.'),
    dict(id='aden', name='Aden', lng=45.03, lat=12.75, fahrten=[5, 6], funktion='Handelsstadt (Teilflotte)', belegt='belegt',
         quelle='Ma Huan; arabische Chronik der Rasuliden', hinweis='Die Teilflotte von 1421 führte wahrscheinlich Zhou Man.'),
    dict(id='mogadischu', name='Mogadischu', lng=45.35, lat=2.04, fahrten=[5, 6], funktion='Tributmission, Ostafrika', belegt='belegt',
         quelle='Fei Xin, Xingcha Shenglan; Mingshi', hinweis=''),
    dict(id='brava', name='Brava', lng=44.03, lat=1.11, fahrten=[5, 6], funktion='Tributmission, Ostafrika', belegt='belegt',
         quelle='Fei Xin, Xingcha Shenglan', hinweis=''),
    dict(id='malindi', name='Malindi', lng=40.12, lat=-3.22, fahrten=[5], funktion='Tributmission; Rückführung der Gesandten', belegt='belegt',
         quelle='Mingshi; Dreyer 2007', hinweis='Gesandte aus Malindi brachten 1415/16 Tiere (u. a. eine Giraffe) an den Hof. Die 5. Fahrt brachte sie zurück.'),
    dict(id='dschidda', name='Dschidda / Mekka', lng=39.17, lat=21.48, fahrten=[7], funktion='Gesandtschaft nach Mekka (kleine Gruppe)', belegt='umstritten',
         quelle='Ma Huan, Yingya Shenglan; Ibn Taghribirdi (ägypt. Chronik)', hinweis='Belegt ist: Eine kleine Gruppe (darunter Ma Huan) reiste 1432/33 nach Mekka. Ob Schiffe der Flotte bis Dschidda fuhren oder die Gruppe ein Schiff aus Calicut nutzte, ist umstritten.'),
]

W_AUS = {'seide': 'Seide', 'porz': 'Porzellan', 'lack': 'Lackwaren', 'kupfer': 'Kupfermünzen'}
W_EIN = {'gew': 'Gewürze/Pfeffer', 'edel': 'Edelsteine', 'weih': 'Weihrauch', 'tiere': 'exotische Tiere (z. B. Giraffe)'}


def waren(aus, ein):
    return [{'name': W_AUS[k], 'von_nach': 'ost->west'} for k in aus] + [{'name': W_EIN[k], 'von_nach': 'west->ost'} for k in ein]


QUELLE = 'Ma Huan, Yingya Shenglan (1451); Fei Xin, Xingcha Shenglan (1436); Mingshi 304; Liujiagang- und Changle-Inschrift (1431); Dreyer 2007'

FAHRTEN = [
    dict(nr=1, von=1405, bis=1407,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-java', 'java-palembang', 'palembang-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-quilon', 'quilon-cochin', 'cochin-calicut'),
         stationen='Nanjing/Liujiagang → Changle → Champa → Java → Palembang → Malakka → Semudera → Ceylon → Quilon → Calicut',
         waren=waren(['seide', 'porz', 'lack', 'kupfer'], ['gew', 'edel']),
         hinweis='Ziel war Calicut. Für diese Fahrt nennen die Quellen rund 27.800 Mann. Auf der Rückfahrt 1407 Kampf bei Palembang gegen den Seeräuber Chen Zuyi.'),
    dict(nr=2, von=1407, bis=1409,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-java', 'java-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-quilon', 'quilon-cochin', 'cochin-calicut'),
         abzweige=[dict(name='Teilflotte nach Siam', pfad=LEGS['camau-siam'], belegt='belegt')],
         stationen='Champa → Siam (Teilflotte) → Java → Malakka → Semudera → Quilon → Cochin → Calicut',
         waren=waren(['seide', 'porz', 'kupfer'], ['gew', 'edel']),
         hinweis='Vor allem Rückführung von Gesandten nach Calicut, Cochin, Siam und Java. Keine Landung auf Ceylon. Ob Zheng He selbst mitfuhr, ist umstritten.'),
    dict(nr=3, von=1409, bis=1411,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-java', 'java-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-quilon', 'quilon-cochin', 'cochin-calicut'),
         stationen='Champa → Java → Malakka → Semudera → Ceylon (Galle) → Quilon → Cochin → Calicut',
         waren=waren(['seide', 'porz', 'kupfer'], ['gew', 'edel']),
         hinweis='In Malakka entstand ein befestigtes Lager. 1411 Kampf auf Ceylon: König Alakeshvara wurde gefangen genommen und nach Nanjing gebracht.'),
    dict(nr=4, von=1413, bis=1415,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-java', 'java-palembang', 'palembang-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-cochin', 'cochin-calicut', 'calicut-hormuz'),
         abzweige=[dict(name='Malediven', pfad=LEGS['calicut-male'], belegt='belegt')],
         stationen='Champa → Java → Palembang → Malakka → Semudera → Ceylon → Cochin → Calicut → Malediven → Hormuz',
         waren=waren(['seide', 'porz', 'kupfer'], ['gew', 'edel']),
         hinweis='Erstmals über Indien hinaus bis Hormuz am Persischen Golf. Der Übersetzer Ma Huan fuhr zum ersten Mal mit.'),
    dict(nr=5, von=1417, bis=1419,
         pfad=join(*START, 'changle-quanzhou', 'quanzhou-champa', 'champa-camau', 'camau-java', 'java-palembang', 'palembang-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-cochin', 'cochin-calicut', 'calicut-hormuz', 'hormuz-aden', 'aden-mogadischu', 'mogadischu-brava', 'brava-malindi'),
         stationen='Quanzhou → Champa → Java → Palembang → Malakka → Semudera → Ceylon → Cochin → Calicut → Hormuz → Aden → Mogadischu → Brava → Malindi',
         waren=waren(['seide', 'porz', 'lack', 'kupfer'], ['gew', 'edel', 'weih', 'tiere']),
         hinweis='Rückführung von Gesandten bis Arabien und Ostafrika. 1419 brachte die Flotte Tiere wie Giraffen an den Hof. Die Reihenfolge Hormuz → Aden → Ostafrika ist schematisch; wahrscheinlich fuhren Teilflotten getrennt.'),
    dict(nr=6, von=1421, bis=1422,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-malakka', 'malakka-semudera', 'semudera-galle', 'galle-komorin', 'komorin-cochin', 'cochin-calicut', 'calicut-hormuz'),
         abzweige=[dict(name='Teilflotte nach Dhofar und Aden', pfad=join('calicut-dhofar', 'dhofar-aden'), belegt='belegt'),
                   dict(name='Teilflotte nach Ostafrika (Mogadischu, Brava)', pfad=join('calicut-male', 'male-mogadischu', 'mogadischu-brava'), belegt='umstritten')],
         stationen='Semudera (Teilung) → Ceylon → Cochin → Calicut → Hormuz; Teilflotten nach Dhofar, Aden, Mogadischu, Brava',
         waren=waren(['seide', 'porz'], ['weih', 'edel', 'tiere']),
         hinweis='Die Flotte brachte Gesandte aus 16 Ländern heim und teilte sich bei Semudera. Welche Wege die Teilflotten genau nahmen und welche Orte Zheng He selbst besuchte, ist unklar.'),
    dict(nr=7, von=1431, bis=1433,
         pfad=join(*START, 'changle-champa', 'champa-camau', 'camau-java', 'java-palembang', 'palembang-malakka', 'malakka-semudera', 'semudera-galle', 'galle-beruwala', 'beruwala-komorin', 'komorin-calicut', 'calicut-hormuz'),
         abzweige=[dict(name='Teilflotte nach Bengalen (Hong Bao)', pfad=LEGS['semudera-bengalen'], belegt='belegt'),
                   dict(name='Gesandtschaft Richtung Dschidda/Mekka', pfad=LEGS['calicut-dschidda'], belegt='umstritten')],
         stationen='Champa → Surabaya → Palembang → Malakka → Semudera → Beruwala → Calicut → Hormuz; Teilflotten nach Bengalen und Richtung Dschidda/Mekka',
         waren=waren(['seide', 'porz', 'kupfer'], ['gew', 'edel', 'weih']),
         hinweis='Letzte Fahrt, angeordnet von Kaiser Xuande. Zheng He starb vermutlich 1433 auf der Rückfahrt (manche Angaben nennen 1435).'),
]

DATA = {
    '_hinweis': 'Erzeugt mit build_zhenghe.py. Verläufe schematisch. Nur belegte Stationen; Unsicheres = umstritten.',
    'info': {
        'titel': 'Die Fahrten des Zheng He (1405–1433)',
        'absaetze': [
            'Kaiser Yongle (Ming-Dynastie, regierte 1402–1424) gab die Fahrten in Auftrag. Admiral war Zheng He. Sieben große Flottenfahrten führten durch Südostasien und den Indischen Ozean bis nach Arabien und Ostafrika.',
            'Zweck: Tribut- und Prestigediplomatie. Gesandte brachten Geschenke, fremde Herrscher schickten Gesandte und Tribut an den Kaiserhof. Es ging um Ansehen und Kontakte, nicht um Eroberung.',
            'Flottengröße: Für die 1. Fahrt nennen Ming-Quellen rund 27.800 Mann. Die Zahl der Schiffe schwankt in den Quellen (z. B. 62 große Schiffe, mit Begleitschiffen weit mehr). Wie groß die „Schatzschiffe“ wirklich waren, ist umstritten; die überlieferten Maße (über 120 m Länge) halten viele Forschende für übertrieben.',
            'Ende: Nach Yongles Tod stoppte Kaiser Hongxi 1424 die Fahrten. Kaiser Xuande ließ 1431–1433 noch eine letzte Fahrt durchführen, danach gab es keine solchen Flotten mehr. Privaten Seehandel verbot das Seeverbot (Hai jin) schon seit 1371; es blieb bestehen und wurde erst 1567 gelockert.',
        ],
        'quelle': QUELLE,
    },
    'verbindungen': [],
    'orte': [],
    'ereignisse': [
        dict(jahr=1405, titel='Erste Fahrt beginnt', text='Kaiser Yongle befiehlt im Juli 1405 die erste Fahrt. Im Herbst bricht die Flotte von Nanjing auf.', belegt='belegt'),
        dict(jahr=1407, titel='Kampf bei Palembang', text='Die Flotte besiegt den Seeräuber Chen Zuyi und bringt ihn nach Nanjing.', belegt='belegt'),
        dict(jahr=1411, titel='Kampf auf Ceylon', text='Zheng He nimmt König Alakeshvara gefangen und bringt ihn nach Nanjing.', belegt='belegt'),
        dict(jahr=1414, titel='Giraffe am Kaiserhof', text='Gesandte aus Bengalen schenken dem Kaiser eine Giraffe. Am Hof wird sie als glückbringendes Fabeltier (Qilin) gefeiert. Ursprünglich stammte sie wohl aus Ostafrika.', belegt='belegt'),
        dict(jahr=1419, titel='Tiere aus Afrika und Arabien', text='Die 5. Fahrt kehrt zurück, u. a. mit Giraffen, Zebras und Löwen als Geschenke für den Kaiser.', belegt='belegt'),
        dict(jahr=1424, titel='Fahrten gestoppt', text='Kaiser Yongle stirbt. Sein Nachfolger Hongxi stoppt die teuren Fahrten.', belegt='belegt'),
        dict(jahr=1431, titel='Inschriften von Liujiagang und Changle', text='Vor der letzten Fahrt lässt Zheng He Inschriften aufstellen, die alle Fahrten beschreiben.', belegt='belegt'),
        dict(jahr=1433, titel='Letzte Rückkehr', text='Die 7. Fahrt kehrt im Juli 1433 zurück. Zheng He stirbt vermutlich 1433 auf der Rückfahrt (manche Angaben: 1435).', belegt='umstritten'),
    ],
    'waren': [
        dict(name='Seide', von_nach='ost->west', weg='Ausfuhr Chinas (Geschenke, Handel)', quelle='Ma Huan'),
        dict(name='Porzellan', von_nach='ost->west', weg='Ausfuhr Chinas', quelle='Ma Huan; Funde an der ostafrikanischen Küste'),
        dict(name='Lackwaren', von_nach='ost->west', weg='Ausfuhr Chinas (Geschenke)', quelle='Ming-Geschenklisten; Umfang unklar'),
        dict(name='Kupfermünzen', von_nach='ost->west', weg='Ausfuhr Chinas', quelle='Ma Huan (Java, Palembang)'),
        dict(name='Gewürze/Pfeffer', von_nach='west->ost', weg='Einfuhr aus Indien und Südostasien', quelle='Ma Huan (Calicut, Cochin)'),
        dict(name='Edelsteine', von_nach='west->ost', weg='Einfuhr aus Ceylon und Hormuz', quelle='Ma Huan'),
        dict(name='Weihrauch', von_nach='west->ost', weg='Einfuhr aus Arabien (Dhofar, Aden)', quelle='Ma Huan'),
        dict(name='exotische Tiere (z. B. Giraffe)', von_nach='west->ost', weg='Geschenke aus Bengalen, Arabien, Ostafrika', quelle='Mingshi; Shen Du, Giraffenbild (1414)'),
    ],
}

for f in FAHRTEN:
    nr = f['nr']
    DATA['verbindungen'].append({
        'id': 'zh%d' % nr, 'nr': nr,
        'name': '%d. Fahrt (%d–%d)' % (nr, f['von'], f['bis']),
        'art': 'see', 'pfad': f['pfad'], 'von': f['von'], 'bis': f['bis'],
        'reiche': ['ming'], 'vermittler': ['Zheng He und Ming-Flotte'],
        'abzweige': f.get('abzweige', []),
        'stationen': f['stationen'],
        'richtung_waren': f['waren'],
        'belegt': 'belegt', 'quelle': QUELLE,
        'hinweis': f['hinweis'] + ' Verlauf schematisch; die Rückfahrt nahm meist denselben Weg.',
    })

for o in ORTE:
    fs = o.pop('fahrten')
    von = min(f['von'] for f in FAHRTEN if f['nr'] in fs)
    o.update(an=[['zh%d' % n, 'ganz'] for n in fs], von=von, bis=1433, vermittler=o['funktion'])
    DATA['orte'].append(o)

# ---------------- Prüfung: Seewege über Land? ----------------
try:
    from shapely.geometry import shape, LineString, Point
    land = json.load(open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))
    geom = shape(land['geometry'] if 'geometry' in land else land['features'][0]['geometry']).buffer(0)
    ports = [Point(o['lng'], o['lat']).buffer(0.9) for o in ORTE]
    for name, p in LEGS.items():
        for a, b in zip(p, p[1:]):
            seg = LineString([a, b])
            for pt in ports: seg = seg.difference(pt)
            if not seg.is_empty and seg.intersects(geom):
                l = seg.intersection(geom).length
                if l > 0.25: print('  über Land: %s %s->%s (%.2f°)' % (name, a, b, l))
except ImportError:
    print('(shapely fehlt: keine Landprüfung)')

# ---------------- Kontext: Ming-Reich, Hauptstädte, Europa zur gleichen Zeit ----------------
# Ming-Reich um 1405–1440, grob von Hand gezeichnet (ohne Tibet, Mongolei, Tarimbecken; Grenze etwa entlang der Großen Mauer,
# Liaodong bis zum Yalu, Yunnan einschließlich der Grenz-Tusi). Jiaozhi (Nordvietnam) war 1407–1427 Ming-Provinz.
MING = [
    dict(name='Ming-Reich (vereinfacht)', von=1400, bis=1454, pts=[
        (98.2,39.8),(102.5,38.4),(104.0,37.6),(105.9,39.0),(106.7,38.9),(108.5,37.9),(110.6,38.9),(111.5,40.3),(114.0,40.8),
        (116.5,40.8),(118.5,40.5),(119.8,40.1),(121.0,41.8),(123.5,42.5),(124.8,40.6),(124.3,39.6),(122.5,38.8),(122.8,37.0),
        (123.0,31.0),(122.0,28.0),(119.0,24.0),(117.0,22.8),(114.0,21.5),(111.0,20.6),(111.5,18.0),(108.5,17.8),(108.0,20.0),
        (108.3,21.5),(107.9,21.5),(106.7,22.8),(105.3,23.3),(103.9,22.5),(102.2,22.4),(101.7,21.2),(100.2,21.5),(98.6,24.1),
        (97.6,24.8),(98.6,27.5),(99.2,28.3),(101.5,30.0),(102.5,31.5),(103.2,33.0),(104.0,34.2),(102.5,34.8),(101.6,36.0),
        (101.5,37.5),(100.0,38.5)]),
    dict(name='Jiaozhi (Nordvietnam, Ming-Provinz 1407–1427)', von=1407, bis=1428, pts=[
        (102.2,22.4),(103.9,22.5),(105.3,23.3),(106.7,22.8),(107.9,21.5),(108.5,21.0),(107.0,19.5),(106.2,17.8),(105.6,16.8),
        (104.6,17.6),(104.4,18.6),(103.8,20.5),(102.5,21.5)]),
]
def ming_regionen():
    feats = []
    try:
        from shapely.geometry import Polygon, mapping, shape
        from shapely.geometry.polygon import orient
        land = shape(json.load(open(os.path.join(HERE, 'data', 'land.json'), encoding='utf-8'))['geometry']).buffer(0)
        frueher = None
        for i, m in enumerate(MING):
            g = Polygon(m['pts']).buffer(0).intersection(land)
            if frueher is not None: g = g.difference(frueher)   # keine Überlappung
            frueher = g if frueher is None else frueher.union(g)
            polys = [orient(q, sign=-1.0) for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon' and q.area > 0.004]
            gm = mapping(polys[0]) if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': [mapping(q)['coordinates'] for q in polys]}
            gm = json.loads(json.dumps(gm, default=float))
            def rnd(o): return [rnd(x) for x in o] if isinstance(o, (list, tuple)) else round(o, 3)
            feats.append({'type': 'Feature', 'properties': {'id': 'ming%d' % i, 'reich': 'ming', 'name': m['name'], 'von': m['von'], 'bis': m['bis'], 'art': 'kern'},
                          'geometry': {'type': gm['type'], 'coordinates': rnd(gm['coordinates'])}})
    except ImportError:
        print('(shapely fehlt: Ming-Reich ohne Küstenanpassung übersprungen)')
    return feats

DATA['ming'] = {
    'name': 'Ming-Reich', 'farbe': '#c9772b',
    'regionen': ming_regionen(),
    'hauptstaedte': [
        dict(name='Nanjing (Hauptstadt bis 1421)', lng=118.78, lat=32.06, von=1400, bis=1420),
        dict(name='Peking (Hauptstadt ab 1421)', lng=116.40, lat=39.90, von=1421, bis=1453),
    ],
    'hinweis': 'Fläche stark vereinfacht. Die Ming beherrschten weder Tibet noch die Mongolei; die Nordgrenze verlief etwa entlang der Großen Mauer.',
}
# Europa zur gleichen Zeit: portugiesische Entdeckungsfahrten (zum Vergleich); route = schematischer Seeweg ab Lissabon bzw. Lagos
DATA['europa'] = [
    dict(jahr=1415, titel='Portugal erobert Ceuta', ort='Ceuta', lng=-5.32, lat=35.89, belegt='belegt',
         route=[[-9.14,38.69],[-9.55,38.55],[-9.3,37.4],[-9.0,36.95],[-7.6,36.8],[-6.4,36.3],[-5.7,35.97],[-5.32,35.91]],
         text='Ein portugiesisches Heer erobert die Hafenstadt Ceuta in Nordafrika. Prinz Heinrich („der Seefahrer“) ist dabei. Danach beginnen die Fahrten an der afrikanischen Küste entlang.',
         quelle='Gomes Eanes de Zurara, Crónica da Tomada de Ceuta (um 1450)'),
    dict(jahr=1419, titel='Madeira wird erreicht', ort='Madeira', lng=-16.92, lat=32.65, belegt='belegt',
         route=[[-8.67,37.08],[-9.4,36.6],[-11.5,35.3],[-14.3,33.8],[-16.25,33.12],[-16.7,32.8],[-16.9,32.66]],
         text='Portugiesische Seefahrer (João Gonçalves Zarco, Tristão Vaz Teixeira) erreichen Porto Santo und Madeira. Ab etwa 1420/25 werden die Inseln besiedelt.',
         quelle='Zurara, Crónica dos feitos da Guiné (1453)'),
    dict(jahr=1427, titel='Azoren entdeckt', ort='Azoren', lng=-25.67, lat=37.74, belegt='umstritten',
         route=[[-9.14,38.69],[-9.6,38.6],[-13.0,38.4],[-18.0,38.1],[-22.5,37.9],[-25.4,37.76]],
         text='Ein portugiesischer Seefahrer (Diogo de Silves) sichtet die Azoren mitten im Atlantik. Das Jahr stammt aus einer Seekarte von 1439 und ist nicht ganz sicher; besiedelt wurden die Inseln ab etwa 1432/39.',
         quelle='Seekarte des Gabriel de Vallseca (1439)'),
    dict(jahr=1434, titel='Gil Eanes umsegelt Kap Bojador', ort='Kap Bojador', lng=-14.48, lat=26.13, belegt='belegt',
         route=[[-8.67,37.08],[-9.4,36.4],[-9.8,34.5],[-10.3,31.6],[-10.6,30.0],[-11.9,28.6],[-13.4,27.6],[-14.3,26.9],[-14.75,26.13]],
         text='Gil Eanes fährt als erster Europäer an Kap Bojador vorbei, das lange als Grenze des befahrbaren Meeres galt. Seine Schiffe sind viel kleiner als die Flotte des Zheng He.',
         quelle='Zurara, Crónica dos feitos da Guiné (1453)'),
]

out = os.path.join(HERE, 'data', 'zhenghe.json')
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(DATA, fh, ensure_ascii=False, indent=1)
print('geschrieben:', out, len(DATA['verbindungen']), 'Fahrten,', len(DATA['orte']), 'Häfen')
