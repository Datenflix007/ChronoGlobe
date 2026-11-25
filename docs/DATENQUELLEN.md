# Datenquellen für Straßen und Städte

Stand der Prüfung: 20.11.2026. Geprüft wurden ORBIS und die Datensatzliste von Project MERCURY. Ziel war, Straßen und Städte des Tafelbilds aus offenen Forschungsdaten zu speisen.

## Kurzfassung

| Bereich | Derzeit im Tafelbild | Geprüfte Alternative | Entscheidung |
|---|---|---|---|
| Straßenverlauf | Itiner-e (2025), 819 vereinfachte Hauptstraßen | ORBIS-Straßennetz (2012/2014) | **Itiner-e bleibt**: genauer, neuer, teils datiert |
| Zeitangaben der Straßen | regionales Modell + Itiner-e-Belege | ORBIS: keine Jahreszahlen | ORBIS hilft hier nicht |
| Schiffsverkehr (Küste, Hochsee, Flüsse) | **ORBIS** (seit 20.11.2026, Schalter „Schiffsverkehr (ORBIS)“) | – | **umgesetzt**, siehe unten |
| Reisezeiten | – | ORBIS: Geschwindigkeit und Kosten je Strecke | möglicher neuer Baustein |
| Seidenstraße der Han (Linien, Stationen) | **Hu/Yan/Zhang 2018** (seit 20.11.2026, Schalter „Seidenstraße der Han (Stationen)“) | – | **umgesetzt**, siehe unten |
| Römische Städte | 94 Orte, von Hand gesetzt (`data/reiche.json` → `orte`) | Hanson, Cities Database (1388 Städte, mit Anfangsjahr) | möglicher **Ersatz/Ergänzung**, Lizenz vorher klären |
| Ortsnamen, Koordinaten | von Hand | Pleiades (Ortsverzeichnis), ORBIS-Orte | zum Abgleich geeignet |

## ORBIS – The Stanford Geospatial Network Model of the Roman World

- Website: https://orbis.stanford.edu/ (Walter Scheidel, Elijah Meeks, Stanford University Libraries)
- Daten: GitHub `emeeks/orbis_v2`, Lizenz des Repositorys **MIT**. Kartenkacheln der Website: AWMC, CC BY-NC 3.0 (werden hier nicht verwendet).
  - `sites_extended.csv`: 670 Orte mit Name, Rang (60–100), Koordinaten, Provinz, heutigem Land
  - `base_routes.geojson`: 1215 Strecken zwischen diesen Orten, Feld `t`:

    | `t` | road | coastal | overseas | upstream | downstream | ferry |
    |---|---|---|---|---|---|---|
    | Anzahl | 627 | 411 | 69 | 54 | 49 | 5 |

    Dazu kommen je Strecke `e` (Kosten) und `s` (Geschwindigkeit) des Verkehrsmodells.
- **Zeitbezug:** keiner. ORBIS bildet das Netz als Momentaufnahme um 200 n. Chr. ab. Es gibt keine Bau- oder Nutzungsjahre.
- **Straßen:** Die 627 Straßenstrecken ergeben gemessen rund 60 000 km. Sie verbinden nur die ORBIS-Orte und beruhen auf dem Barrington Atlas (2000). Itiner-e ist neuer, deutlich dichter (laut Projektangaben knapp 300 000 km) und für einen Teil der Abschnitte datiert. Ein Wechsel brächte deshalb weniger Genauigkeit und keine Zeitangaben.
- **Was ORBIS zusätzlich bietet:**
  - Reisezeiten und Kosten, z. B. „Wie lange dauerte eine Reise von Rom nach Londinium?“
  - See- und Flussrouten (Küstenschifffahrt, Hochsee, Flüsse)

  Für ein Tafelbild zur Leitfrage „Zentrum der Welt?“ wäre das didaktisch reizvoll, etwa als Entfernungskarte ab Rom.

## Project MERCURY – Datensatzliste

- https://projectmercury.eu/datasets/ (Computational Modelling in Roman Studies). Eine Sammlung von Links zu offenen Datensätzen, ohne eigene Daten.
- Für Straßen und Städte relevant:
  - **Transport system (Orbis)** → siehe oben.
  - **Roads:** AWMC/DARMC-Straßenshapefiles (Barrington Atlas). Ebenfalls ohne Datierung und älter als Itiner-e.
  - **Urban areas / Cities: Hanson (2016), Cities Database (OXREP)**
    - Download: http://oxrep.classics.ox.ac.uk/oxrep/docs/Hanson2016/Hanson2016_Cities_OxREP.csv
    - Inhalt: 1388 Orte mit städtischen Merkmalen (100 v. Chr. – 300 n. Chr.). Zu jedem Ort gibt es antiken und heutigen Namen, Provinz, Rang im Barrington Atlas (1–5), Koordinaten, Bibliografie, **Anfangsjahr** (`Start Date`, bei allen gefüllt) und Endjahr (`End Date`, nur bei 38 gefüllt).
    - Abgleich: 92 der 94 römischen Orte des Tafelbilds liegen höchstens 0,2° von einem Hanson-Ort entfernt.
    - **Lizenz:** „Terms and Conditions of Use for Oxford University Research Archive“, keine freie Lizenz wie CC BY. Gefordert ist die Zitierung von Datenbank und Monografie. Vor einer Übernahme in dieses öffentliche Repository ist zu klären, ob Weitergabe und Veröffentlichung erlaubt sind.
    - Zitierung: Hanson, J. W. (2016): Cities Database (OXREP databases), Version 1.0, DOI 10.5287/bodleian:eqapevAn8; Hanson, J. W. (2016): An Urban Geography of the Roman World, 100 B.C. to A.D. 300, Oxford.
  - **Places (Pleiades):** https://pleiades.stoa.org/downloads – Ortsverzeichnis der antiken Welt (alle Orte des Barrington Atlas), Lizenz CC BY 3.0. Geeignet zum Abgleich von Namen und Koordinaten.

## Seidenstraße: Quellen aus China und weitere Links (geprüft 20.11.2026)

**Umgesetzt: Seidenstraße der Han**
- Quelle: Hu Yumeng, Yan Bo, Zhang Ping: 两汉丝绸之路交通数据集 / *Traffic data of the Silk Road in the Han dynasty*. China Scientific Data 3 (2018), Nr. 3, DOI 10.11922/csdata.2018.0016.zh.
- Daten: Science Data Bank, DOI 10.57760/sciencedb.611 (früher 10.11922/sciencedb.611), **Lizenz CC BY 4.0**.
- Inhalt:
  - 14 rekonstruierte Hauptlinien von Chang’an bis ans Mittelmeer.
  - Verkehrspunkte der Westlichen (202 v.–8 n. Chr.) und Östlichen Han (25–220 n. Chr.) mit Typ (Hauptstadt, Kommandantur, Kreissitz, Poststation, Pass, Fährstelle, Brücke, Siedlung …), Zeitraum und Namen.
- Aufbereitung `build_han_seidenstrasse.py` → `data/han_seidenstrasse.json`:
  - 269 Stationen; gleiche Orte beider Perioden sind zusammengefasst.
  - Linien vereinfacht (0,015°).
  - Die Lage wird über den chinesischen Namen aus dem Shapefile übernommen.
  - 5 Einträge mit seltenen Schriftzeichen ließen sich keiner Lage zuordnen und fehlen.
- Download: Das Archiv (RAR) der Science Data Bank enthält Dateien mit GBK-kodierten Namen. Windows-`tar` entpackt es erst, wenn die Namen ersetzt sind (Hilfsskript im Arbeitsordner, nicht im Repository).
- Darstellung:
  - Linien hellgold, Stationen als Punkte nach Typ (Poststation blau, Pass orange, Haupt- und Verwaltungssitze gold).
  - Infokarte mit der Rolle für Handel und Verkehr.
  - Sichtbar mit eingeblendetem Han-Reich von 202 v. bis 220 n. Chr.

**Geprüft, (noch) nicht übernommen**

| Link | Inhalt | Warum nicht |
|---|---|---|
| sciengine …70310B4E… (Cheng/Zhang 2018) | Reisen von 15 Reisenden der Mongolenzeit 1218–1353 (u. a. Marco Polo, Ibn Battuta), GIS | **seit 21.11.2026 übernommen** (Reiseberichte), siehe `docs/HANDELSNETZE.md` |
| sciengine …FD62111B… (Xu/Zhang 2018) | Tang-Seidenstraße 618–907, Linien und Stationen jahrgenau | **seit 21.11.2026 übernommen**, siehe `docs/HANDELSNETZE.md` |
| PMC6936881 (Lancuo u. a. 2019) | Modell der Tang–Tibet-Straße (Least-Cost-Pfad) | Tang-Zeit; Modell, keine Belegdaten |
| Frachetti u. a. 2017 (Nature, UCL-Manuskript) | Hochlandrouten der Seidenstraße aus Weidewegen der Nomaden (Flussakkumulation) | Modellergebnis ohne frei verfügbare Geodaten; als Hintergrund für Schülertexte nutzbar |
| dlyj 10.11821/dlyj020210210 | GIS-Rekonstruktion der Südlichen Seidenstraße in China | Seite lädt Inhalte per Skript; Daten nicht frei zugänglich gefunden |
| dlyj 52820 (Lin u. a. 2022) | Dichte und Wirkung der Seidenstraßen (Regression; Knoten Rom, Chang’an, Samarkand) | Auswertung, keine Geodaten; Ergebnisse taugen als Hintergrund |
| LSE WP 371 (Cheng 2024) | Transportkosten Yangtze-Region vs. England, Ming–Qing; Auseinanderlaufen nach 1700 | betrifft 1600–1800, außerhalb der Zeitleiste |
| gis.harvard.edu/china-historical-gis (CHGIS) | Verwaltungseinheiten Chinas ab 222 v. Chr. | Seite blockiert automatische Abrufe; Lizenz vor Übernahme prüfen |

## Handels- und Verkehrsnetze (seit 21.11.2026)

Eigenes Menü mit Landwegen, Wasserwegen und Reiseberichten. Ausführlich mit Datenmodell, Download und Prüfergebnissen: `docs/HANDELSNETZE.md`.

| Netz | Quelle | Lizenz |
|---|---|---|
| Weihrauchstraße Petra – Gaza | Zohar, Erickson-Gini 2019; Zenodo 10.5281/zenodo.3413625; Zeitraum nach UNESCO 1107 | CC BY 4.0 |
| Seidenstraße der Tang | Xu, Zhang 2018; Science Data Bank 10.57760/sciencedb.587 | CC BY 4.0 |
| Straßen der Levante (VIA-TARIQ) | Pažout 2026, Version 1.1; Zenodo 10.5281/zenodo.21981430 | CC BY 4.0 |
| Wegenetz der islamischen Welt | al-Ṯurayyā Gazetteer nach G. Cornu 1983 | CC BY 4.0 |
| Reisende der Mongolenzeit | Cheng, Zhang 2018; Science Data Bank 10.57760/sciencedb.622 | CC BY 4.0 |

Nicht übernommen:
- ArcGIS-Weihrauchstraßen: keine offene Lizenz.
- Ming-Postnetz: CC0, aber späte Ming-Zeit nach 1453, daher zurückgestellt.
- Südliche Seidenstraße, CHGIS, Kaiserkanal (GeoDOI), OWTRAD: nicht verfügbar bzw. nicht prüfbar.
| silkroad.fudan.edu.cn | Seidenstraßen-GIS der Fudan-Universität | nur Web-Anwendung, kein Download |
| zenodo.org/records/22734751 | – | Abruf blockiert (403); Inhalt nicht geprüft |

## Was eine Übernahme bedeuten würde

1. **Städte aus Hanson** (nach Klärung der Lizenz):
   - Ein Ort erscheint ab seinem Anfangsjahr, aber nur, solange sein Gebiet zum Römischen Reich gehört (wie bisher).
   - Die Zoomstufen ergeben sich aus dem Barrington-Rang (1 → Weltstadt … 4/5 → nur ganz nah).
   - Die Liste ist rund 15-mal so lang wie die bisherige. Die Ausdünnung nach Zoomstufe bleibt daher wichtig.
   - Grenze: Hanson deckt nur das Römische Reich ab. Han-China und die Nachbarreiche bleiben von Hand gepflegt.
2. **Schiffsverkehr aus ORBIS – umgesetzt** (`build_orbis.py` → `data/orbis_schiff.json`):
   - Übernommen werden nur die Schiffsstrecken, nicht die Straßen: 505 Strecken (349 Küste, 56 Hochsee, 5 Fähren, 95 Flüsse). Stromauf und stromab zwischen denselben Orten sind zu einer Flussstrecke zusammengefasst.
   - Die Endpunkte der Schiffsstrecken tragen ORBIS-Kennungen, die um 100 000, 200 000 usw. versetzt sind. Kennung modulo 100 000 ergibt den Ort in `sites_extended.csv`.
   - **Zeitregel:** ORBIS hat keine Jahreszahlen. Eine Strecke ist sichtbar, solange beide Endpunkte in einer römischen Fläche aus `data/reiche.json` liegen (Puffer 0,3°, weil Häfen knapp außerhalb der vereinfachten Küstenflächen liegen können). Beispiele: Rutupiae–Gesoriacum 43–410, Strecken im Westen bis 476. Das ist eine Darstellungsregel und kein Beleg für den Beginn des Verkehrs. Die Infokarte sagt das ausdrücklich.
   - Nur im Abschnitt Antike und nur, wenn das Römische Reich eingeblendet ist.
   - **Darstellung:** einfarbig hellblau (wie bei den Straßen keine Farbcodierung nach Art), Flüsse blasser. Die Art (Küste, Hochsee, Fähre, Fluss) steht im Tooltip und in der Infokarte.
   - Sichtbare Strecken: 250 v. Chr. 50, 100 v. Chr. 248, 30 n. Chr. 447, 117 n. Chr. 505, 470 n. Chr. 380.
3. **Reisezeiten aus ORBIS** (MIT):
   - neuer Schalter, z. B. „Reisezeit ab Rom“, mit Einfärbung der Orte nach Tagen
   - einfaches Wegenetzmodell aus `base_routes.geojson`, nicht das vollständige ORBIS-Modell mit Jahreszeiten und Verkehrsmitteln
4. **Straßen bleiben Itiner-e.** ORBIS und AWMC/DARMC wären ungenauer und haben keine Zeitangaben (siehe `docs/STRASSEN_ZEITMODELL.md`).

## Frühe Hochkulturen: Ägypten, Nubien, Ägäis, Athen und Sparta (geprüft 25.11.2026)

Erzeugt mit `build_fruehe_kulturen.py` → `data/fruehe_reiche.json`. Gebiete sind nur angedeutet; Jahreszahlen sind gerundet und folgen der konventionellen Chronologie. Ereignisse mit geprüfter Belegstelle tragen das Feld `quelle` (im Editor unter „Bisher“ sichtbar). „PDF-S.“ meint die Seite im heruntergeladenen PDF, nicht die gedruckte Seitenzahl.

| Thema | Quelle | Was daraus übernommen bzw. geprüft wurde |
|---|---|---|
| Nubien, Kerma, Grenze des Neuen Reiches | Kuckertz, „Meroe and Egypt“, UCLA Encyclopedia of Egyptology 2021 | Kerma ca. 2400–1450 v. Chr.; Eroberung bis Kurgus (zwischen 4. und 5. Katarakt) zu Beginn der 18. Dynastie → Gebiet „Nubien bis Kurgus“ |
| Megiddo | Nelson, The Battle of Megiddo (1913), S. 5 | „Jahr 23“ Thutmosis’ III. (Annalen von Karnak); absolutes Jahr 1457 v. Chr., nach anderer Chronologie 1482 |
| Hyksos, Auaris | Breasted, A History of Egypt (1905), Buch IV | Einnahme von Auaris nach der Biografie des Ahmose, Sohn der Ebana. Kamose steht dort nicht (Inschriften später gefunden) → ohne Beleg |
| Sethos I., Merenptah, Seevölker | Breasted, Ancient Records of Egypt III (1906), § 574; History of Egypt, S. 464–480 | Feldzüge Sethos’ I. (Reihenfolge unsicher); Merenptahs Gegner Ekwesch, Teresch, Lukka, Scherden, Schekelesch; Peleset unter Ramses III. |
| Götter Ägyptens | Wilkinson, „Anthropomorphic Deities“, UEE 2008, S. 5 und 7 | Triaden Amun–Mut–Chons (Theben) und Ptah–Sachmet–Nefertem (Memphis); Synkretismus Amun-Re |
| Kreta | Journal of Archaeological Research (2023), Bronzezeitliches Kreta, S. 13 und 15 | Zerstörungen 1500–1450 v. Chr., danach Knossos unter Griechisch sprechender Elite (Linear B), Ende im späten 14. Jh.; Thera: hohe gegen niedrige Datierung, Forschung neigt zur Mitte des 16. Jh.; Gipfelheiligtümer Juktas und Petsofas |
| Thera, Kollaps um 1200 | Knapp/Manning, „Crisis in Context“, AJA 120 (2016) | Ursachen des Zusammenbruchs als Bündel und umstritten; Manning vertritt die hohe Thera-Datierung |
| Mykenische Paläste | Bennet, „Palaces and their Regions“, PDF-S. 9; Middleton, Durham-Diss. 2008, Bd. I | Pylos mit zwei Provinzen; Zusammenbruch der Paläste um 1200 v. Chr. |
| „Dunkle Jahrhunderte“ | Kotsonas, „Politics of Periodization“, AJA 120 (2016) | Begriff als umstritten gekennzeichnet |
| Perserkriege, Ionischer Aufstand | Kagan, Yale CLCV 205, Handout „The Persian Wars“; Joyner, ECU 2010 | 499 Aufstand (Athen 20, Eretria 5 Schiffe), 494 Lade und Sepeia, 501 erste Erwähnung des Peloponnesischen Bundes, Didyma 494/3 zerstört |
| Delisch-Attischer Seebund | Kagan, Yale CLCV 205, Handout „The Athenian Empire“ | 478/7 Gründung, 460 Talente, Kasse auf Delos, Naxos um 470, Kasse 454/3 nach Athen, Kalliasfrieden 449 (umstritten), Dreißigjähriger Frieden 445, Schlangensäule mit 31 Städten |
| Peloponnesischer Krieg | Thukydides (Übers. Crawley); Xenophon, Hellenika (Loeb 1918) | Sphakteria (Thuk. IV), Sizilien (VI–VII), Aigospotamoi (Hell. II 1), Königsfrieden, Leuktra |
| Zweiter Attischer Seebund | Marshall, The Second Athenian Confederacy (1905) | 378/7 Gründung (Aristoteles-Dekret, Synhedrion), Bundesgenossenkrieg 357–355 |

Nicht abrufbar waren am 25.11.2026 (Server lieferte HTML statt PDF): ISAC OIP 8 und SAOC 12, Murnane (Medinet Habu), Brown-Reader, UMass- und Utah-Vorlesungen, OAPEN (Knodell). Sie sind nicht eingeflossen.

## Griechenland und Rom nach dem Grundkurs „Alte Geschichte“ (seit 25.11.2026)

Maßgeblich für Griechenland und Rom ist der Grundkurs „Alte Geschichte“ (Skript des Instituts für Altertumswissenschaften, FSU Jena, WS 2022/23, Redaktionsstand 14.10.2022; im Folgenden GK). Übernommen sind nur Eckdaten und Epochen, in eigenen Worten; Ereignisse tragen im Feld `quelle` die Seite im GK. Das Skript selbst liegt nicht im Repository.

| Bereich | GK | Umsetzung |
|---|---|---|
| Epochen | S. 4, 57, 66 | Leisten „Griechenland“ und „Rom“ über den Reichsspuren und Epochenhinweis in den Infokarten (nur freier Modus); `epochen` in `data/fruehe_reiche.json` |
| Minoer, Mykener | S. 3, 57 | Kreta ab 2000 v. Chr., Aufgabe des Palastes von Knossos um 1200 (frühere Datierung ins 14. Jh. als umstritten genannt); Palastzeit 1450–1200, Nachpalastzeit bis 1050 |
| Athen, Sparta, Theben | S. 58–63 | Archonten 683/82, Drakon, Solon, Peisistratiden, Kleisthenes 508/07; Messenische Kriege; Kasse des Seebunds 455/54, Kalliasfrieden 450/49 (umstritten), Dreißigjähriger Frieden 446/45, Eurymedon um 466; neues Reich „Theben“ (371–335) mit Leuktra, Mantineia, Messenien frei 369 |
| Persien | S. 60, 62 | Ausdehnung in Schritten: Meder 550, Lyder 547/46, Babylon 539, Indus unter Dareios I.; Kunaxa 401, Knidos 394, Königsfriede 386 |
| Makedonien, Diadochen, Hellenismus | S. 63–65 | Philokrates 346, Lamischer Krieg, Diadochenkriege, Königsproklamationen 306, Antigoniden, Syrische Kriege, Makedonische Kriege, Apameia 188, Tag von Eleusis 168 |
| Rom | S. 66–80 | Gebiete ab 753 (legendär) in Schritten bis 300 v. Chr. (`build_fruehe_kulturen.py`), Ereignisse von der Königszeit bis 476 (`build_reiche.py`); Sardinien/Korsika 237, Magnesia 189 (GK nennt „am Mäander“; gemeint ist Magnesia am Sipylos), Gallien 58–51 |
| Karthago, Parther, Sasaniden | S. 65, 68, 72, 76–80 | Ereignisse in den Infokarten der Nachbarreiche |
| Alexanderzug | S. 63, 86 | Ein durchgehender Weg in acht Etappen, Stationen (`alexander_stationen`), Umkehr am Hyphasis 326; Siwa nach Plut. Alex. 27 (GK S. 86) |
| Zitat am Hyphasis | – | Arr. an. 5,26, nur der geprüfte Teilsatz; deutsch nach der gemeinfreien englischen Übersetzung von E. J. Chinnock (London 1884), abgerufen über Wikisource („The Anabasis of Alexander/Book V/Chapter XXVI“) [Übers. d. Verf.]. Der griechische Text war am 25.11.2026 nicht abrufbar (Perseus). Hinweis auf die Gestaltung antiker Reden (Thuk. 1,22, GK S. 81) |
| Völkerwanderung | S. 3, 77–79 | Beginn „um 375“ mit Hinweis, dass das Jahr nicht belegt ist; Rheinübergang 406/07; Gotenfoedus 382; ergänzt: Theoderich nach Italien 489–493, Westgoten nach Vouillé (507) nach Spanien, Langobarden 568; Schlachten Soissons 486 und Vouillé 507; je Zug ein **Auslöser** und **Stationen unterwegs** (Überfälle, Plünderungen, Belagerungen) mit Quellenstelle (u. a. Ammianus, Zosimos, Hieronymus Brief 123, Hydatius, Jordanes, Prokop, Paulus Diaconus); Motive, die in der Forschung umstritten sind, als umstritten gekennzeichnet (`VW_KONTEXT` in `build_reiche.py`) |

## Griechische Poleis und Kolonisation (seit 25.11.2026)

Erzeugt mit `build_poleis.py`; die Rohdaten liegen nur lokal unter `quellen/lokal/poleis/` (per `.gitignore` ausgeschlossen).

| Datei | Quelle | Lizenz |
|---|---|---|
| `data/ebenen/griechische-poleis.json` (911 Poleis), `data/ebenen/delisch-attischer-seebund.json` (274 Mitglieder) | POLIS, Stanford University (digitale Fassung von Hansen/Nielsen, *An Inventory of Archaic and Classical Poleis*, 2004): `polis.stanford.edu/data/master_data_11_19_2013.csv` | **keine Lizenz angegeben** („frei zugänglich für akademische Nutzung“). **Vor einer Veröffentlichung klären** (Anfrage an das Stanford Classics Department) oder auf Pleiades-Koordinaten (CC BY) umstellen. |
| `data/kolonisation.json` (157 Züge Mutterstadt → Kolonie) | Anhang 27 von Hansen/Nielsen 2004, digitalisiert von D. Krasne (v1.0, 2026) | CC BY 4.0 |

Darstellungsregeln: Poleis erscheinen ab ihrem Gründungsdatum (nur für Kolonien bekannt, sonst ab 650 v. Chr.) bis 323 v. Chr. Gründungsdaten in der Notation des Inventars („C6m“ = Mitte 6. Jh.) werden auf ein Jahr umgerechnet und als unsicher markiert. Kolonisationswege sind schematisch: berechnet über Wegpunkte auf See, nicht überliefert. 18 kurze Gründungen unter 60 km (teils ins Binnenland, z. B. Akrai von Syrakus) verlaufen direkt.

## Mittelalter 480–1453 (seit 25.11.2026)

`build_mittelalter.py` → `data/mittelalter_reiche.json`: Byzanz (als Fortsetzung des Reichs „rom“), Langobarden, Kalifate, al-Andalus, christliche Reiche Iberiens, chinesische Dynastien, Liao und Jin, Mongolen, Seldschuken, Fatimiden/Ayyubiden/Mamluken, frühe Osmanen, Ostfranken/HRR, Frankreich, England, Rus, Bulgarien, Ungarn, Polen, Nordindien. Nur angedeutet: von Hand gesetzte Umrisse und gerundete Handbuchdaten; keine Belegstellen je Ereignis. Für den Unterricht als Orientierung gedacht, nicht als Grenzkarte.

Ergänzt am 25.11.2026, damit Mitteleuropa keine Lücken mehr hat:
- Frankenreich 487–843 in Stufen (Chlodwig, Vouillé 507, Burgund/Provence 534/37, Friesland 734, Septimanien 759, Langobardenreich 774, Awarenkriege 796, Sachsen 804) als Teil des Reichs „franken“; Westgoten in Gallien enden 507.
- Neu: Awaren (568–796), Lotharingien und Burgund/Arelat (843–1032), Regnum Italiae (843–962), Kirchenstaat (756–1453), Fürstentum Benevent (bis 1077, beim Reich „langob“), Sizilien und Süditalien (902–1453), Serbien (1180–1453), Litauen (1240–1453), Deutscher Orden (1230–1453), englische Besitzungen in Frankreich (1154–1453), Galizien-Wolhynien (1240–1349).
- Umrisse neu gezogen entlang der Linien, die die Handbücher nennen: Vertrag von Verdun 843 (Schelde, Maas, Saône, Rhône), Elbe und Saale, Enns, Alpenhauptkamm, Pyrenäen, Karpatenbogen, Erzgebirge, Sudeten, Böhmerwald. Stufen für HRR (880, 962, 1032, 1150, 1335), Polen (1138, 1320, 1349), Ungarn (1102 mit Kroatien), Bulgarien (Krum, Simeon, Samuel, Iwan Assen II.), Rus (Kiewer Rus, Nordost-Rus unter der Goldenen Horde), Mongolen-Khanate.
- Zeitlich berichtigt: Byzanz in Italien erst im Gotenkrieg (535–552), Thrakien nach 1354 osmanisch (Adrianopel 1369), Seldschuken in Bagdad ab 1055, sasanidisches Mesopotamien bis 637 und Medien bis 642.

## Grenzen bereinigen: `build_grenzen.py` (seit 25.11.2026)

Die drei Reichsdateien (`data/reiche.json`, `data/fruehe_reiche.json`, `data/mittelalter_reiche.json`) entstehen unabhängig. `build_grenzen.py` läuft danach und schreibt sie zurück:

1. Grenzen in der Nähe (≤ 0,35°) großer Flüsse und Gebirgskämme werden auf diese Linien gelegt (Saumstücke von 0,6° Länge; jedes Stück gehört ganz zu dem Reich, das es überwiegend bedeckt). Flächen unter 1,5 Grad² (Stadtstaaten, Inseln) bleiben unverändert.
2. Schmale Landstreifen (≤ 1°) zwischen gleichzeitigen Reichen werden etwa auf der Mittellinie geteilt. Große unbesetzte Räume bleiben leer, wenn dort kein Reich belegt ist (z. B. Westalpen vor 15 v. Chr., Walachei um 1000).
3. Gleichzeitige Flächen überdecken sich nicht mehr. Vorrang haben Rom und Han, sonst die kleinere, genauer gezeichnete Fläche; die unterlegene verliert das Gebiet nur für die Jahre der Überschneidung (Zeitabschnitte werden geteilt, neue ids ab 9001). Oberhoheit (Tribut, Lehnshoheit, z. B. Goldene Horde über die Rus) steht im Text, nicht als zweite Fläche. Flächen der Art „einfluss“ bleiben unberührt.
4. Küsten exakt nach `data/land.json`.

Prüfung ohne Änderung: `python build_grenzen.py --pruefen` (Stichjahre alle 25 Jahre; Rückgabewert 1 bei Überlappungen über 0,05 Grad²; kleinere sind Rundungsreste; schmale Lücken zwischen Nachbarn werden nur gemeldet, weil manche historisch richtig sind). Koordinaten werden auf 0,01° (≈ 1 km) gerundet. Stand nach dem Lauf: keine Überlappungen außer Rundungsresten; von 978 schmalen Lücken (Stichjahre) bleiben rund 200, meist historisch freie Räume (Alpen vor der Eroberung, Steppengrenzen, Walachei), einige Grenzstreifen sind noch zu prüfen.

## Historische Geographie: `build_geographie.py` → `data/geographie.json` (seit 25.11.2026)

| Bestandteil | Quelle | Hinweis |
|---|---|---|
| Flussläufe | Natural Earth 1:10 Mio., *Rivers + lake centerlines* und *Rivers Europe* (gemeinfrei, naturalearthdata.com) | heutige Läufe; antike Läufe wichen besonders in Deltas und Schwemmebenen ab |
| Gebirge | Natural Earth 1:10 Mio., *Geography regions* (Umrisse der Gebirge) | Kammlinie = Mittelachse des Umrisses, schematisch |
| Namen, Auswahl | Grundkurs „Alte Geschichte“, Skript FSU Jena, WS 2022/23, Kap. 8 „Historische Geographie“ (S. 41–42) und Karten S. 43–45; Hydaspes und Hyphasis S. 63; Elbe S. 71; Ebro-Grenze S. 68 | Einträge ohne Seitenangabe sind ergänzt und in der Anzeige so gekennzeichnet (Huang He, Jangtse, Haimos, Kaukasos, Zagros, Pindos, Libanos, Mare Ionium, Hellespontos, Parnassos, Vesuv, Ätna) |
| Landschaften | Skript S. 42 („Wichtige antike Landschaften, Provinzen und Städte“) und Karten S. 43–45 | Beschriftungspunkte von Hand gesetzt |

Die Natural-Earth-Daten lädt das Skript einmalig nach `quellen/lokal/naturalearth/` (nicht im Repository). Die App lädt nur `data/geographie.json` vom eigenen Server.

## Archäologische Funde, Alexanderzug

- `data/ebenen/archaeologische-funde.json`: 33 Funde mit Entstehungszeit, Fundjahr und Aufbewahrungsort (Renfrew/Bahn 2016, Van De Mieroop 2016, George 2003 zum Gilgamesch-Epos, Shaw 2000).
- Alexanderzug in `build_fruehe_kulturen.py` (acht Etappen nach Arrian, *Anabasis* I–VII; Wege schematisch).
