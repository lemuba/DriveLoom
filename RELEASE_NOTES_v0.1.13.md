# DriveLoom v0.1.13 — Fortschritt beim POI-Download

## Änderungen

- Während eines Länderdownloads zeigt das POI-Panel den bereits heruntergeladenen Datenumfang und, falls Geofabrik die Gesamtgröße übermittelt, einen Prozentwert mit Fortschrittsbalken. Die Anzeige wird während des Downloads ungefähr alle fünf Sekunden aktualisiert.
- Ist die Gesamtgröße unbekannt, bleibt der Balken unbestimmt; die geladene Menge wird trotzdem angezeigt.
- Nach dem Download zeigt das Panel **„POIs werden importiert …“** mit einem unbestimmten Balken. 100 % Download bedeuten noch keinen abgeschlossenen Katalogimport. Der vorherige vollständige Katalog bleibt bis zum erfolgreichen Abschluss verfügbar.
- Die Kartendatei heißt nun `driveloom-card-0.1.13.js`. Die Löschfunktion aus v0.1.12 bleibt enthalten.

## Bedienung

Im POI-Panel **Regionaler POI-Katalog** öffnen und ein Land auswählen. Nach dem Speichern erscheinen unter dem Katalogstatus die Downloadmenge und gegebenenfalls der Fortschrittsbalken. Anschließend wird die Importphase separat angezeigt.

## Manuelle Veröffentlichung

Den ZIP-Inhalt in das GitHub-Repository übernehmen und die alte versionierte Datei `driveloom-card-0.1.12.js` entfernen. Den neuen Commit als **v0.1.13** taggen und diese Notizen für das GitHub-Release verwenden. Das ZIP kann zusätzlich als Release-Asset hochgeladen werden. Nach dem Installieren Home Assistant neu starten. Eine YAML-Ressource auf `/driveloom/driveloom-card-0.1.13.js?v=0.1.13` ändern.

## Prüfung und Grenzen

Ein mehrteiliger Testdownload prüft die übertragenen Bytes, die Fortschrittsmeldungen und das Größenlimit. Die Frontend-Anzeige für bekannte und unbekannte Gesamtgrößen sowie die Importphase wird getestet. Die vollständigen Tests und das entpackte ZIP werden ebenfalls geprüft. Ein echter großer Download und die iPad-/iPhone-Darstellung müssen in deiner Home-Assistant-Installation praktisch geprüft werden.
