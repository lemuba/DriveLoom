# DriveLoom v0.1.11 — Länderindex und POI-Panel korrigiert

## Änderungen

- Der Geofabrik-Länderindex wird vollständig eingelesen, auch wenn Home Assistant die Antwort in mehreren Blöcken liefert. Der Fehler `Expecting property name enclosed in double quotes ... char 8191` aus v0.1.10 wird damit behoben. Die Größenbegrenzung von 8 MiB bleibt bestehen.
- Das aufklappbare Feld **Regionaler POI-Katalog** erhält eine deutliche Schaltfläche mit Pfeil. Fehler beim Länderindex stehen direkt über der Auswahlliste; **Weitere Länder laden** versucht den Abruf ohne Neustart erneut.
- Checkboxen und Ländernamen stehen kompakt nebeneinander. Die Auswahlliste soll auf iPad und Smartphone ohne seitliches Scrollen bedienbar sein.
- Die Karte verwendet jetzt `driveloom-card-0.1.11.js`. Die Funktionen aus v0.1.10 bleiben enthalten.

## Einrichtung

Im POI-Panel **Regionaler POI-Katalog → Länder auswählen** öffnen. Nach dem Laden die gewünschten Länder markieren und die Einstellungen speichern. Falls nur Deutschland und Bundesländer sichtbar sind, **Weitere Länder laden** wählen; bei erneuter Fehlermeldung den angezeigten Text prüfen. Ein erster Länderimport kann je nach Dateigröße lange dauern und benötigt zusätzlichen Speicherplatz.

## Manuelle Veröffentlichung

Den Inhalt des ZIPs in das GitHub-Repository übernehmen; die alte Datei `driveloom-card-0.1.10.js` aus dem Repository entfernen. Den neuen Commit mit **v0.1.11** taggen und diese Notizen für das GitHub-Release verwenden. Das ZIP kann zusätzlich als Release-Asset hochgeladen werden. Nach dem Installieren Home Assistant neu starten. Eine YAML-Ressource auf `/driveloom/driveloom-card-0.1.11.js?v=0.1.11` ändern.

## Prüfung und Grenzen

Der mehrteilige Indexabruf und seine Größenbegrenzung sind mit Testdaten geprüft. Die Python- und Frontend-Tests sowie das entpackte ZIP werden erneut geprüft. Ein echter Abruf über deine Home-Assistant-Verbindung, der Import großer Länder und die Darstellung auf deinem iPad erfordern danach einen Praxistest.
