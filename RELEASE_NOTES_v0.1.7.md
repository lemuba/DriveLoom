# DriveLoom v0.1.7 — POI-Sprung und Kartenansicht

## Änderungen

- Im GPS-Follow-Hinweis springen **⇈** und **⇊** direkt zur letzten beziehungsweise ersten Gruppe der bereits geladenen POIs. Die einfachen Pfeile blättern weiterhin um jeweils einen Treffer. Alle vier Tasten haben 44 px große Touchflächen und stehen kompakt rechts neben der Liste.
- Ein Tipp auf einen POI zeigt ihn samt Umgebung auf der Karte. Die Zielkachel bietet **Zurück zum Fahrzeug** und **Google Maps öffnen**. Die Google-Maps-Adresse bleibt fest mit dem gewählten POI verbunden, auch wenn sich die Reihenfolge der Treffer währenddessen ändert.
- Während der POI-Ansicht werden GPS-Position und POIs weiter aktualisiert; die Kamera bleibt am betrachteten Ziel. **Zurück zum Fahrzeug** stellt den vorherigen GPS-Follow-Zoom und die aktuelle Fahrtrichtung wieder her. In der Testansicht im Stand geht es zur vorherigen Kartenposition zurück.
- Der POI-Detailzoom ist im POI-Panel zwischen 12 und 20 wählbar und wird mit einer global gespeicherten POI-Vorlage übernommen. Bisherige Vorlagen verwenden Zoom 16.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt nun `driveloom-card-0.1.7.js?v=0.1.7`.

## Manuelle Veröffentlichung und Installation

Den entpackten ZIP-Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.6.js` entfernen. Den neuen GitHub-Commit als `v0.1.7` taggen, diesen Release-Text verwenden und `DriveLoom_0.1.7_GitHub_HACS.zip` selbst als Release-Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.7.js?v=0.1.7` ersetzen.

## Prüfung und Grenzen

Automatisierte Tests sowie Syntax- und Paketprüfungen laufen lokal und erneut nach frischer ZIP-Extraktion. Die Bedienung auf einem echten iPhone mit Home Assistant bleibt praktisch zu prüfen. Die Pfeile blättern nur durch bereits geladene, passende POIs; die Distanz ist Luftlinie und keine Routenberechnung.
