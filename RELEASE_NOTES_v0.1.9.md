# DriveLoom v0.1.9 — Regionaler POI-Katalog

## Änderungen

- Ein großer regionaler POI-Katalog wird aus einem Geofabrik-OSM-Auszug auf Home Assistant aufgebaut. Zur Auswahl stehen Deutschland und einzelne Bundesländer.
- Die Aktualisierung läuft nach lokalem Zeitplan (Uhrzeit und Intervall von 1 bis 30 Tagen) und kann manuell ausgelöst werden. Der letzte vollständige Katalog bleibt bei Fehlern erhalten.
- Räumliche Abfragen liefern POIs im sichtbaren Kartenausschnitt und in Fahrzeugnähe. Die bisherigen Vorlagen, Textfilter, Cluster und die 1–3 Vorschläge im GPS-Follow funktionieren weiter.
- Für die Karte sind 500 bis 10.000 Treffer pro Abfrage einstellbar; beim erstmaligen Aktivieren sind 3.000 voreingestellt. Der Server kann mehr POIs speichern.
- Ladestationen kommen weiterhin von Open Charge Map. Ohne regionalen Katalog bleibt die bisherige Live-Suche verfügbar.

## Einrichtung

Im POI-Panel **Regionaler POI-Katalog** öffnen, Region sowie Uhrzeit und Intervall wählen und speichern. Ein Administrator muss dies ausführen. Der erste Import kann bei Deutschland mehrere Gigabyte herunterladen, lange dauern und zusätzlich Platz für die temporäre Datei und Datenbank brauchen. Die Statusanzeige informiert über Anzahl, Zeitpunkt und Fehler. Die eingestellte HA-Zeitzone bestimmt die Uhrzeit.

## Manuelle Veröffentlichung

Den ZIP-Inhalt entpacken und in das GitHub-Repository übernehmen. Die alte Frontend-Datei `driveloom-card-0.1.8.js` entfernen. Den neuen Commit als **v0.1.9** taggen und diesen Text als GitHub-Release-Notizen verwenden; das HACS-Zip selbst als Release-Asset hochladen. Nach Installation Home Assistant neu starten. Bei YAML-Ressourcen den Eintrag `/driveloom/driveloom-card-0.1.9.js?v=0.1.9` verwenden.

## Prüfumfang und Grenzen

Importer und räumliche SQLite-Abfrage wurden mit mehreren Tausend Test-POIs geprüft; die bestehenden Frontend-Abläufe und das frisch extrahierte ZIP werden ebenfalls geprüft. Ein echter Geofabrik-Download, die Installation von `osmium` in Home Assistant und das Verhalten auf Safari/iPhone sind anschließend in deiner HA-Installation praktisch zu prüfen. Knoten und Wege sind enthalten; POIs, die nur als OSM-Multipolygon-Relation erfasst sind, fehlen. Eine Bundeslandregion endet an ihrer Grenze, auch wenn der Suchradius weiter reicht.
