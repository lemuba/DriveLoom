# DriveLoom v0.1.3 — POIs in Fahrtrichtung

## Änderungen

- Während GPS-Follow zeigt ein kompakter Kartenhinweis das nächstliegende geladene POI in Fahrtrichtung mit deutlich gekennzeichneter Luftdistanz.
- Alle aktiven POI-Kategorien und Betreiberfilter zählen gemeinsam. Bei beispielsweise IONITY, EnBW und Tesla wird der nächste passende Standort aus allen drei Netzen vorgeschlagen.
- Der Hinweis wechselt nicht bei kleinen Entfernungsunterschieden und verschwindet nach dem Passieren, bei fehlender oder veralteter Fahrtrichtung sowie außerhalb von GPS-Follow.
- Ein Tipp öffnet zuerst eine Bestätigung. Erst „Google Maps öffnen“ übergibt das gewählte Ziel zur Navigation; abhängig vom Gerätestandort kann Google Maps zunächst eine Routenvorschau zeigen.
- Der Schalter „POI-Hinweis im GPS-Follow anzeigen“ befindet sich im POI-Panel und wird gespeichert.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt jetzt `driveloom-card-0.1.3.js?v=0.1.3`.

## Installation

Den entpackten Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.2.js` entfernen. Danach den Tag `v0.1.3` auf dem neuen Commit erstellen, diesen Release-Text verwenden und `DriveLoom_0.1.3_GitHub_HACS.zip` selbst als Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.3.js?v=0.1.3` ersetzen.

## Prüfung und Grenzen

Automatisierte Tests und Paketprüfungen laufen lokal und nach frischer ZIP-Extraktion. Ein iPhone-/CarPlay-Fahrttest und die Bedienung auf echten Home-Assistant-Geräten bleiben praktische Tests. Die Luftdistanz berücksichtigt weder Straßennetz noch Zufahrt oder Verfügbarkeit einer Ladestation.
