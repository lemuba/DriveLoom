# DriveLoom v0.2.0b6 — Beta

## Korrektur zur „Suche voraus“

Der Screenshot aus v0.2.0b5 zeigt HTTP 404 nach einer Gemini-Suche. DriveLoom hatte Gemini 2.5 Flash-Lite fest gewählt. Google beschränkt dieses Modell für neue API-Projekte. Die Beta erklärt diesen Fall nun konkret.

- **Schnelllader ohne KI suchen** verwendet die bereits konfigurierte Open Charge Map. Der Standtest mit Kartenmitte, Fahrtrichtung, Suchweite und Mindestleistung für CCS funktioniert auch ohne Gemini-Schlüssel.
- Wenn Gemini bei einer Ladesäulensuche HTTP 404 meldet, wechselt DriveLoom zur selben Open-Charge-Map-Suche. Ein kostenpflichtiges KI-Modell wird nicht verwendet.
- Die lokalen Treffer haben Kartenpins, Quellenlink und Google-Maps-Navigation. **Ad-hoc-Preise sind unbekannt.** Maximalpreis und freie Suchkriterien werden lokal nicht geprüft. Es findet kein Preisvergleich statt.
- Für Orte und Veranstaltungen bleibt die Gemini-Websuche von der Verfügbarkeit des 2.5-Modells für den eigenen Schlüssel abhängig. Hier zeigt DriveLoom beim 404 die Einschränkung an, statt einen scheinbar erfolgreichen unbelegten Treffer zu liefern.

## Manuell auf GitHub veröffentlichen

1. `DriveLoom_0.2.0b6_GitHub_HACS.zip` herunterladen und entpacken. Den Inhalt des ZIP-Stammverzeichnisses in dein GitHub-Repository übernehmen. Die alte Datei `custom_components/driveloom/frontend/driveloom-card-0.2.0b5.js` im Repository entfernen; das ZIP enthält nur die neue `driveloom-card-0.2.0b6.js`.
2. Neuen Tag **`v0.2.0b6`** und ein GitHub-Release mit diesen Notes anlegen; als **Pre-release** markieren. Es wird nichts automatisch hochgeladen.
3. Home Assistant neu starten und die Browseransicht neu laden. In YAML-Ressourcen `/driveloom/driveloom-card-0.2.0b6.js?v=0.2.0b6` verwenden.

## Prüfung

Teste im Stand mit „Kartenmitte“, Richtung Süd, CCS und 100 kW. Der lokale Knopf muss eine vorhandene Open-Charge-Map-Konfiguration nutzen. Bei einem lokalen Treffer muss „Preis unbekannt“ erscheinen. Die Google-API bleibt für diesen lokalen Aufruf unbenutzt.

Offline-Frontend- und Backend-Tests sowie zwei ZIP-Prüfungen wurden durchgeführt. Ein echter Gemini-Aufruf und ein Home-Assistant-Browsertest sind ohne deinen API-Schlüssel und deine Installation nicht möglich. Die umfassende Tracking-Testsuite hängt in dieser Umgebung weiterhin an einem bestehenden SQLite-Neustarttest und wird nicht als bestanden gewertet. Der stabile Release `v0.1.14` bleibt unverändert.
