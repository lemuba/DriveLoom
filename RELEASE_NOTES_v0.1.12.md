# DriveLoom v0.1.12 — gespeicherte POI-Kataloge löschen

## Änderungen

- Das POI-Panel zeigt unter **Gespeicherte Kataloge** alle vollständig importierten Länder und Regionen samt belegtem Speicherplatz an. Auch abgewählte Länder bleiben sichtbar.
- Ein Administrator kann eine nicht mehr ausgewählte Katalogdatei nach einer ausdrücklichen Rückfrage löschen. Während eines laufenden Imports ist Löschen gesperrt. Die zentrale `driveloom.db` mit Fahrzeug- und Fahrtdaten wird dabei nicht berührt.
- Durch erneutes Auswählen eines gelöschten Landes startet ein neuer Download und Import. Die übrigen Länder bleiben erhalten.
- Die Kartendatei heißt nun `driveloom-card-0.1.12.js`; alle Verbesserungen aus v0.1.11 sind enthalten.

## Bedienung

Im POI-Panel **Regionaler POI-Katalog** öffnen, das zu löschende Land abwählen und **Katalog-Einstellungen speichern**. Nach Abschluss etwaiger laufender Importe unter **Gespeicherte Kataloge** beim Land auf **Löschen** tippen und die Rückfrage bestätigen. Die angezeigte Größe bezieht sich auf die jeweilige SQLite-Katalogdatei; temporäre Downloads während eines Imports sind darin nicht enthalten.

## Manuelle Veröffentlichung

Den ZIP-Inhalt in das GitHub-Repository übernehmen und die alte versionierte Datei `driveloom-card-0.1.11.js` entfernen. Den neuen Commit als **v0.1.12** taggen und diese Notizen für das GitHub-Release verwenden. Das ZIP kann zusätzlich als Release-Asset hochgeladen werden. Nach dem Installieren Home Assistant neu starten. Eine YAML-Ressource auf `/driveloom/driveloom-card-0.1.12.js?v=0.1.12` ändern.

## Prüfung und Grenzen

Die Dateizuordnung und das gezielte Löschen eines Testkatalogs wurden zusammen mit dem Schutz der zentralen Datenbank geprüft. Python- und Frontend-Tests, Syntax und das entpackte ZIP werden erneut geprüft. Das Verhalten auf deiner Home-Assistant-Installation und auf iPad/iPhone muss anschließend praktisch geprüft werden.
