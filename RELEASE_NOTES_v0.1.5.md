# DriveLoom v0.1.5 — Flexible POI-Anzeige und Fahrtansicht

## Änderungen

- Im POI-Panel lässt sich die Anzahl der gleichzeitig gezeigten Ziele auf **1, 2 oder 3** stellen. Die Auswahl wird gespeichert und gilt auch für die Testansicht im Stand. Bisherige Installationen starten weiterhin mit drei Zielen.
- Die Hinweiskachel sitzt auf dem Smartphone etwas tiefer und hält Abstand zur Kartenquellenangabe.
- Ein Auto-Knopf direkt auf der Karte schaltet die **Fahrtansicht** ein: Kartentitel und beide oberen Bedienreihen verschwinden, die Karte nutzt deren Platz. Der sichtbare Knopf „Bedienleiste anzeigen“ stellt die Steuerung wieder her.
- Beim Umschalten bleiben GPS-Follow, gewählter Zoom und Kartenstil erhalten. Die Kartengröße wird aktualisiert und das Fahrzeug bei aktivem Follow wieder zentriert.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt jetzt `driveloom-card-0.1.5.js?v=0.1.5`.

## Manuelle Veröffentlichung und Installation

Den entpackten ZIP-Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.4.js` entfernen. Den neuen GitHub-Commit als `v0.1.5` taggen, diesen Release-Text verwenden und `DriveLoom_0.1.5_GitHub_HACS.zip` selbst als Release-Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.5.js?v=0.1.5` ersetzen.

## Prüfung und Grenzen

Automatisierte Tests und Paketprüfungen laufen lokal und nach frischer ZIP-Extraktion. Die genaue Darstellung auf dem iPhone und die Bedienung während einer echten Fahrt bleiben praktische Prüfungen. Die angezeigten Kilometer sind Luftlinien und keine Straßenentfernungen.
