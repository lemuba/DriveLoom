# DriveLoom v0.1.10 — mehrere Länder und Installationsfix

## Änderungen

- Behebt den Startfehler von v0.1.9: `osmium==4.3.1` ist keine Pflichtabhängigkeit mehr. Der enthaltene PBF-Importer funktioniert ohne zusätzliche Python-Pakete; falls `osmium` bereits in Home Assistant verfügbar ist, wird dessen schnellerer Import verwendet.
- Im POI-Panel lassen sich mehrere Länder und Regionen aus dem Geofabrik-Index gleichzeitig auswählen. Deutschland und seine Bundesländer bleiben verfügbar. Die Auswahl wird für alle gespeicherten POI-Vorlagen gemeinsam genutzt.
- Für jedes Land werden Importstand, Anzahl und Fehler angezeigt. Die tägliche Uhrzeit und das Intervall gelten gemeinsam; manuelle Aktualisierung ist für alle oder einzeln möglich. Datenbanken werden nacheinander und atomar aufgebaut; ein gescheiterter Import erhält den letzten vollständigen Stand.
- Treffer aus ausgewählten Ländern werden gemeinsam abgefragt und anhand ihrer OSM-Kennung zusammengeführt. Ladestationen bleiben bei Open Charge Map. Ohne Länderauswahl bleibt die bisherige Live-Suche aktiv.
- Ein bereits vorhandener v0.1.9-Katalog wird nach Möglichkeit in das neue Dateiformat übernommen. Die Kartendatei heißt nun `driveloom-card-0.1.10.js`.

## Einrichtung

Im POI-Panel **Regionaler POI-Katalog** öffnen, die gewünschten Länder markieren, Uhrzeit und Intervall wählen und speichern. Dafür sind Administratorrechte erforderlich. Die Länderliste benötigt beim ersten Abruf Zugriff auf den Geofabrik-Index. Die erste Aktualisierung großer Länder lädt mehrere Gigabyte und kann mit dem eingebauten Parser deutlich länger dauern. Es wird Platz für Download und neue Datenbank benötigt; Importstatus und Fehler erscheinen pro Land.

## Manuelle Veröffentlichung

Das HACS-ZIP entpacken und **dessen Inhalt** in das GitHub-Repository übernehmen. Alte versionierte Dateien wie `driveloom-card-0.1.8.js` und `driveloom-card-0.1.9.js` im Repository entfernen, sodass nur die neue Kartendatei verbleibt. Einen neuen Commit mit Tag **v0.1.10** erstellen und diese Datei als GitHub-Release-Notizen verwenden. Das ZIP kann zusätzlich als Release-Asset hochgeladen werden. Nach der Installation Home Assistant neu starten; bei YAML-Ressourcen `/driveloom/driveloom-card-0.1.10.js?v=0.1.10` eintragen.

## Prüfung und Grenzen

Der paketfreie Import wurde mit einer komprimierten PBF-Testdatei für Knoten und Wege geprüft; räumliche Abfrage, Frontend-Verhalten, Python-Syntax und das entpackte ZIP werden ebenfalls geprüft. Ein großer echter Geofabrik-Download sowie ein Home-Assistant-Start auf deiner Installation müssen dort praktisch geprüft werden. OSM-Multipolygon-Relationen ohne eigenen Knoten oder Weg bleiben unberücksichtigt. Beim eingebauten Parser ist für große Länder mit langer Importdauer und erheblichem Speicherbedarf zu rechnen; mehrere ausgewählte Länder vergrößern den belegten Speicher entsprechend.
