# Grundregeln für Schülertexte und Belege

Diese Regeln gelten für `data/texte.json`, `data/literatur.json` und die abgelegten Quellenseiten unter `quellen/`.

1. **Zitierweise.** Belege werden nach dem Merkblatt „Zitation“ des Historischen Instituts der FSU Jena gesetzt (Vorgaben der Vierteljahrshefte für Zeitgeschichte):
   - Belege stehen als Anmerkungen (Endnoten unter dem Text) mit fortlaufender Zählung.
   - Bei der ersten Nennung steht der Vollbeleg, danach der Kurztitel (Nachname, erstes sinngebendes Substantiv, Seite).
   - „Vgl.“ steht bei sinngemäßer Übernahme, „Ebd.“ bei demselben Titel wie in der vorigen Anmerkung.
   - Bei Sekundärzitaten steht „zit. nach“.
   - Fremdsprachige Zitate werden übersetzt und als „[Übers. d. Verf.]“ gekennzeichnet.
   - Antike Quellen werden nach Stellen zitiert (z. B. Plin. nat. 6,104).
2. **Mindestens zwei unabhängige Fachtitel** (Monografie, Handbuch, Fachaufsatz) je Text. Antike Quellen zählen nicht mit.
3. **Nur Geprüftes.** Jede Sachaussage hat eine Anmerkung, deren Belegstelle wörtlich auf der angegebenen Seite steht. Seitenangaben werden nie aus dem Gedächtnis gesetzt. Was sich nicht belegen lässt, entfällt und wird im Bericht aufgeführt.
4. **Ablage.**
   - `quellen/oeffentlich/`: Seitentexte gemeinfreier Werke; sie liegen im Repository.
   - `quellen/lokal/`: Seitentexte frei zugänglicher, aber urheberrechtlich geschützter Werke. Sie liegen nur auf dem Rechner der Lehrkraft, sind per `.gitignore` ausgeschlossen und werden nicht veröffentlicht.
   - In `data/literatur.json` steht bei jedem Titel `ablage` und `lizenz`.
5. **Umstrittenes kennzeichnen.** Gegensätzliche Forschungsmeinungen werden als solche benannt („Manche Forscher meinen …, andere …“). Widerlegte Thesen werden nicht als Tatsache dargestellt.
6. **Niveaus.** Jeder Text gibt es in drei Fassungen mit gleichem Sachkern:
   - A: einfach, etwa 80–100 Wörter,
   - B: mittel, etwa 130–160 Wörter,
   - C: anspruchsvoll mit Forschungskontroverse, etwa 180–220 Wörter.

   Zu jedem Text gehören ein Glossar, mindestens eine lizenzfreie Abbildung oder Kartenskizze, zwei Arbeitsaufträge und die Box „Woher wissen wir das?“.
7. **Quellenauszüge (Zitatrecht).** Wörtliche Auszüge sind nur zulässig:
   - aus gemeinfreien Texten, auch in eigener Übersetzung aus dem gemeinfreien Original, oder
   - als kurzes Belegzitat aus geschützten Übersetzungen nach § 51 UrhG, mit vollständiger Quellenangabe und erkennbarem Zitatzweck.

   Längere geschützte Texte werden nur in eigenen Worten zusammengefasst. Abbildungen sind eigene Skizzen oder gemeinfreie bzw. frei lizenzierte Bilder mit Lizenzangabe.
8. **Prüfung.** Vor jeder Veröffentlichung muss `python tools/check_zitate.py` ohne Fehler durchlaufen. Das Skript prüft Belegstellen, Fußnotenzeichen, Wortzahlen und die Zahl der Fachtitel.
9. **Erfundenes kennzeichnen.** Erzählvignetten sind ausdrücklich als erfundene Rahmenerzählung markiert; ihre Sachinhalte sind belegt.
