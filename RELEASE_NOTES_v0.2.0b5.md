# DriveLoom v0.2.0b5 — Beta

## Neu: Suche voraus, manuell und im Stand

- Im POI-Panel gibt es **Suche voraus · manuell**. Speichere Suchvorlagen für Ladestationen, Orte oder Veranstaltungen mit Wunschtext, Zusatzkriterien, Suchweite, Datum sowie optional Mindestleistung und maximalem Ad-hoc-Preis. Die bisherigen POI-Vorlagen bleiben eigenständig.
- Starte die Suche per **Suche testen / jetzt suchen**. Als Startpunkt eignen sich die Fahrzeugposition oder die verschiebbare Kartenmitte. Wähle eine Kompassrichtung oder ein gespeichertes Routenziel; das funktioniert im Stand und erfordert kein aktives GPS-Follow.
- Bis zu zwölf Vorschläge erscheinen als Kartenpins und in der POI-Liste, drei davon in einer kompakten Karte. Antippen zeigt den Ort in der Nähe, einen Quellenlink und die Übergabe an Google Maps. Du kannst einen Treffer einem Reiseordner als eigenen POI zuordnen.
- DriveLoom fragt ausschließlich nach Tastendruck über das HA-Backend bei Gemini 2.5 Flash-Lite mit Google-Websuche an. Der Schlüssel wird nur dort gespeichert. Es gibt keine automatischen Abfragen und keinen Wechsel auf ein anderes, kostenpflichtiges KI-Modell. Ein erreichtes API-Limit zeigt eine Fehlermeldung.

## Einrichtung und Grenzen

1. In **Google AI Studio** ein Projekt **ohne aktivierte Abrechnung** auf dem kostenlosen API-Tarif verwenden und dort einen Gemini-API-Schlüssel anlegen. In DriveLoom im POI-Panel unter **Suche voraus · manuell** den Schlüssel als Home-Assistant-Administrator speichern. Ein Schlüssel aus einem bezahlten Projekt kann kostenpflichtige API-Nutzung auslösen; DriveLoom kann den Abrechnungsstatus des fremden Projekts nicht sicher erkennen.
2. Profil und Richtung wählen. Für einen Standtest die Kartenmitte auf die gewünschte Region schieben, **Kartenmitte** als Startpunkt auswählen und den Suchknopf drücken.
3. Die Richtung zum Routenziel ist ein grober Kompasskurs. Es gibt in dieser Beta keine Straßenkorridor- oder Umwegberechnung. Entfernungen sind Luftlinie. Der KI-Dienst liefert Anhaltspunkte mit Quellenlinks; Koordinaten, Ladeleistung, Preise und Öffnungszeiten müssen vor der Anfahrt geprüft werden. Kein Preis erhält ein grünes Verifikationssignal. Unbekannte Preise werden als unbekannt angezeigt; ein gesetzter Maximalpreis blendet sie nicht aus.
4. Suchergebnisse sind flüchtig. Gespeicherte Suchvorlagen und der API-Schlüssel liegen in der bestehenden DriveLoom-SQLite-Datenbank. Auf dem kostenlosen Google-API-Tarif können Anfragen und Antworten zur Produktverbesserung verwendet werden. DriveLoom übermittelt den gewählten Startpunkt und die Suchkriterien, keine Fahrthistorie.

## GitHub und HACS, manuell

1. `DriveLoom_0.2.0b5_GitHub_HACS.zip` herunterladen und **entpacken**. Den Inhalt des ZIP-Stammverzeichnisses in dein GitHub-Repository übernehmen, insbesondere `custom_components/driveloom`, `hacs.json`, README, Changelog und diese Notes. Die alte Datei `custom_components/driveloom/frontend/driveloom-card-0.2.0b4.js` im GitHub-Repository entfernen; der neue Stand enthält nur `driveloom-card-0.2.0b5.js`.
2. Den **neuen Tag `v0.2.0b5`** und ein GitHub-Release anlegen, diese Notes als Beschreibung verwenden und **„Set as a pre-release“** aktivieren. Du veröffentlichst selbst; lokal wird nichts hochgeladen.
3. In HACS die Beta installieren oder die entpackten Dateien in Home Assistant kopieren. Home Assistant neu starten und den Browser neu laden. Bei YAML-Ressourcen die URL auf `/driveloom/driveloom-card-0.2.0b5.js?v=0.2.0b5` umstellen.

## Prüfen

- Im Stand eine Suchvorlage und einen Kartenmittelpunkt wählen, die Richtung setzen und per Tastendruck suchen. Die KI-Abfrage benötigt einen eigenen gültigen Free-Tier-Schlüssel und Internetzugriff auf Google; Offline-Tests können keine echten Ergebnisse oder den Abrechnungsstatus prüfen.
- Einen Kartenpin antippen, Quelle und Preiswarnung prüfen, zur Liste zurückkehren, Google Maps öffnen und einen Treffer in einen Reiseordner übernehmen.
- Bekannte POI-Vorlagen und GPS-Follow weiter verwenden. Beim API-Limit oder Fehler müssen Karte und bisherige POIs nutzbar bleiben.

Vor der Bereitstellung wurden die Frontend-Tests, die gezielten Backend-Tests und zwei unabhängige ZIP-Prüfungen durchgeführt. Die umfassende Tracking-Testsuite blieb in dieser Ausführungsumgebung bei einem bestehenden SQLite-Neustarttest hängen; sie wurde deshalb nicht als bestanden gewertet. `v0.1.14` bleibt der unveränderte stabile Release.
