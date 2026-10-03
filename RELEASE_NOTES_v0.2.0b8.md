# DriveLoom v0.2.0b8 — Beta

## Neue Funktionen und Änderungen

- **OCPDB · MobiData BW** kann im Lade-POI-Panel als Datenquelle für Deutschland gewählt werden. Stecker, Mindestleistung, Betreiber, bekannte Ad-hoc-Preise, Höchstpreis, Verfügbarkeit und Anzahl freier Ladepunkte sind filterbar. Die Einstellungen werden mit globalen POI-Vorlagen gespeichert und gelten auch für die GPS-Follow-Vorausansicht. Der Status wird dort im Hintergrund ungefähr alle 90 Sekunden aufgefrischt, wenn die Karte sichtbar ist.
- Die **manuelle Schnellladersuche voraus** nutzt OCPDB direkt. Fahrzeug oder Kartenmitte ermöglichen einen Standtest. Ein gespeichertes Routenziel gibt eine grobe Richtung vor, keine echte Straßenroute. Bis zu zwölf Treffer erscheinen als anklickbare POIs mit Preis, Status, Quelllink und Google-Maps-Übergabe. Filter auf Preis verlangen eine eindeutige Ad-hoc-Energiepreis-Zuordnung zum konkreten Ladepunkt; zusätzliche Zeitgebühren sind separat erkennbar. Unbekannte oder veraltete Belegung gilt nicht als frei.
- **Gemini und Tavily sind vollständig aus der aktuellen Suche und Bedienoberfläche entfernt.** Alte, in DriveLoom gespeicherte Schlüssel samt Nutzungszähler werden beim Start gelöscht. Es gibt keine KI-Abfrage und keine KI-Gebühren durch diese Beta. Historische Suchvorlagen für Orte/Veranstaltungen werden in dieser Ladeversion nicht angezeigt; Ladevorlagen bleiben erhalten.
- Betreiber- und Stationswebseiten werden bei vorhandenen Open-Charge-Map-Links getrennt angezeigt. Für die konkret geprüfte PRÄG-Station Öschlesee ist eine separat markierte Drittanbieter-Webseite vom September 2026 verlinkt. Sie ist keine Live-Preisquelle.

**Grenzen:** Ad-hoc-Preis und Verfügbarkeit können sich bis zur Ankunft ändern. OCPDB kann nicht jede deutsche Station vollständig abdecken. Besonders große Suchkreise werden auf 5.000 geladene Datensätze begrenzt und bei abgeschnittenen Ergebnissen im POI-Panel kenntlich gemacht. Das GPS-Panel ordnet nach Luftlinie und Richtung, nicht nach tatsächlichem Routen-Umweg. Der erste OCPDB-Abruf lädt öffentliche Tarifzuordnungen; weitere Abfragen nutzen einen zeitlich begrenzten Cache.

## Manuell auf GitHub veröffentlichen

1. `DriveLoom_0.2.0b8_GitHub_HACS.zip` entpacken und das vollständige Stammverzeichnis in dein GitHub-Repository übernehmen. Eine ältere `driveloom-card-0.2.0b6.js` oder b7-Datei im Repository entfernen. Im ZIP liegt `driveloom-card-0.2.0b8.js`.
2. Den neuen Tag **`v0.2.0b8`** und das GitHub-Release mit diesen Notes erstellen und als **Pre-release** markieren. Den stabilen Tag `v0.1.14` nicht ändern. Es wurde nichts auf GitHub hochgeladen.
3. Home Assistant neu starten und die Karte neu laden. Im YAML-Ressourcenmodus `/driveloom/driveloom-card-0.2.0b8.js?v=0.2.0b8` eintragen.

## Zwei Prüfungen vor der Übergabe

Python-Syntax und Backendtests sowie JavaScript-Syntax und UI-Verhalten wurden offline geprüft. Danach werden ZIP-Inhalt, Dateiversionen, Prüfsumme und das Fehlen aktiver KI-Zugänge nochmals getrennt kontrolliert. Eine echte Home-Assistant-Installation samt GPS-Fahrt und aktuellem OCPDB-Feed ist zusätzlich von dir nach dem Kopieren zu testen.
