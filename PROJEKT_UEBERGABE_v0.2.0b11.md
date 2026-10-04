# Vollständiger Projekt-Übergabe-Prompt: DriveLoom v0.2.0b11

Dieser Text kann zusammen mit dem Projekt-ZIP in eine neue Unterhaltung kopiert werden. Er beschreibt den überprüften Projektstand und die bisherigen Entscheidungen. Lies zuerst den enthaltenen Code und die aktuelle README; älteren Gesprächsnotizen und Release Notes gegenüber hat der tatsächliche Quellstand Vorrang.

---

Du arbeitest mit mir an **DriveLoom**, meiner unabhängigen Home-Assistant-Integration für Fahrzeuge, GPS-Tracking, Analytik, Karten, POIs, Routenplanung und Reiseplanung. Arbeite am vollständigen Projekt im beigefügten ZIP. Die aktuelle Beta ist **v0.2.0b11**, die bisherige stabile Version **v0.1.14**. Ich übernehme die fertigen Dateien selbst nach GitHub und veröffentliche dort einen Pre-release; ändere meine GitHub-Repository-Inhalte oder Tags nicht ohne meinen Auftrag. Beim Erstellen eines neuen Releases erwarte ich ein vollständiges HACS/GitHub-ZIP, passende Versionsverweise, Release Notes, belastbare Tests des Quellstands und eine zweite Prüfung des separat entpackten ZIP. Mache keine unbelegten Aussagen über echte iPad-, Fahrzeug- oder Home-Assistant-Tests.

## Ziele und Arbeitsweise

- DriveLoom bleibt eine Integration im Domain-Namen `driveloom`, keine Kopie von Cardata Analytics. Die Datenbank beginnt unabhängig und liest oder migriert keine Cardata-Daten.
- Baue neue Funktionen in die vorhandene Architektur ein; achte auf vorhandene Einstellungen, Datenbankmigrationen und die stabile Version. Keine unaufgeforderten großen Umbauten.
- Bei Datenquellen, Preisen, Ladeleistung, Belegung und API-Verhalten streng zwischen überprüftem Fakt, begrenzter Stichprobe und Vermutung unterscheiden. Unbekannte Preise und veraltete Verfügbarkeit bleiben explizit unbekannt. Webseiten oder öffentliche Endpunkte erst untersuchen, bevor du eine Integration zusagst.
- Frage zunächst nach meinem Feedback, wenn ich „erstmal nichts machen“ sage. Bei einem klaren Auftrag zu einem neuen Release das Release tatsächlich bauen. Zwischen Fragen zu Konzepten und Implementierungsaufträgen unterscheiden.
- Keine kostenpflichtige oder automatische KI-Abfrage aktivieren. Die aktuelle Beta enthält weder Gemini- noch Tavily-Client oder Schlüssel; eine alte DriveLoom-Suchkonfiguration wird von diesen Schlüsseln bereinigt. Suchprofile bleiben intern, sind aber in der Karte derzeit nicht ausführbar.
- Geheimnisse, API-Schlüssel oder Token aus alten Gesprächen nie in Code, Dokumentation, Tests, Logs oder Übergabetexte übernehmen. Gegebenenfalls alte Schlüssel als kompromittiert ansehen und rotieren lassen.

## Repository und Installation

- GitHub-Projekt laut `manifest.json`: `https://github.com/lemuba/driveloom`; HACS-Basis: `custom_components/driveloom` plus `hacs.json` und Projektdateien im Repository-Stamm. Mindestversion laut Manifest/HACS ist Home Assistant **2026.1.0**.
- `custom_components/driveloom/__init__.py` richtet WebSocket-Befehle, Integrationsdienste, Tracking und die statische Lovelace-Ressource ein. In Lovelace-Storage-Modus wird die Ressourcen-URL automatisch aktualisiert. YAML-Modus muss manuell `/driveloom/driveloom-card-0.2.0b11.js?v=0.2.0b11` als Modul angeben.
- Frontend: `custom_components/driveloom/frontend/driveloom-card-0.2.0b11.js`. Die Datei enthält Analytics- und Map-Card, MapLibre-Karte und UI; sie ist groß, daher kleine, gezielte Änderungen und Verhaltensprüfungen bevorzugen. Bei jedem Beta-Release Dateiname, `CARD_VERSION`, Ressource in `__init__.py`, Manifest, README und Release Notes gemeinsam aktualisieren.
- Die stabile Version 0.1.14 nicht mit der Beta verwechseln. Ein neues Beta-Tag bleibt ein GitHub-Pre-release. Nach dem manuellen Kopieren ins Repository muss die vorherige versionierte JS-Ressource entfernt werden; im neuen ZIP liegt nur die neue JS-Datei.

## Architektur und Dateien

| Bereich | Wichtige Datei(en) | Aufgabe |
|---|---|---|
| Integration und Fahrzeuge | `__init__.py`, `config_flow.py`, `runtime.py`, `sensor.py`, `select.py`, `const.py` | Konfiguration, Fahrzeugdaten und Home-Assistant-Einbindung |
| Analytik | `controller.py`, `trip_analytics.py`, `analytics_repair.py`, `soc_filter.py`, `date.py` | Zeiträume, Verbrauch, Fahrten und Korrekturen |
| GPS | `tracking.py`, `gps_sources.py`, `trip_folders.py` | Live-Punkte, Telefon-GPS, historische Fahrten und Ordner |
| Allgemeine POIs | `poi.py`, `poi_templates.py` | Geografische Suche, Open Charge Map, globale Vorlagen und Filter |
| Regionale OSM-Daten | `poi_catalog.py`, `pbf_reader.py` | Geofabrik-Index, Download, PBF-Import, Zeitplan und räumliche Abfragen |
| Deutsche Ladepunkte | `ocpdb.py`, `ocpdb_cache.py` | Öffentliche OCPDB/OCPI-Abfragen, Tarif-/EVSE-Zuordnung, Status und SQLite-Suchgebietscache |
| Reiseplanung | `travel.py` | Reiseordner, eigene POIs, Notizen, Dokumente, Export/Restore und Ortssuche |
| Routen und Suche | `route_data.py`, `smart_search.py` | Gespeicherte Zwischenziele und inaktive historische Suchprofile |
| UI-Zustand | `preferences.py`, Frontend-JS | Pro Benutzer gesicherte Kartenpräferenzen und Browseransicht |
| Persistenz | `db.py` | SQLite-Hauptdatenbank und Schlüssel/Wert-Speicher |

Die vorhandenen WebSocket-Handler werden in `__init__.py` registriert; Dateitransfers des Reise-Archivs sind gechunked. Netzwerkzugriffe laufen, wo vorgesehen, serverseitig über Home Assistant, damit die Lovelace-WebView nicht an CORS scheitert. Blockierende Import- und SQLite-Arbeit gehört in HA-Executor-Jobs. Die Karte verwendet MapLibre und arbeitet mit getrennten Markern/Layern für Fahrzeuge, POIs, eigene Reise-POIs, Routen und Tracking. Vor einer neuen Darstellung auch Sichtbarkeit, Layer-Neuaufbau nach Stilwechsel, Popup-Interaktion und mobile Layouts prüfen.

## Datenhaltung und Sicherung

- `<HA-Konfiguration>/.storage/driveloom.db`: GPS-, Fahrten-, Analyse-, Reise-Metadaten, Reiseordner, eigene POIs, Zuordnungen/Notizen, Vorlagen und UI-Präferenzen. HA verwaltet seine Config Entries, Dashboards und Registry-Daten getrennt.
- `.storage/driveloom-documents.db`: hochgeladene Dokument-Inhalte als SQLite-BLOB-Chunks. Metadaten und Ordnerbezüge liegen in der Hauptdatenbank. Keine einzelne per-Datei-Obergrenze im DriveLoom-Modell; konfigurierbare Gesamtquote startet bei 100 MiB pro Reise oder entsprechender oberster Struktur. PDF/Bilder/Text können im UI vorab angezeigt werden; Office-Dateien haben Download/Öffnung in einer passenden App. Verschieben ändert Beziehungen, nicht die Inhalte.
- `.storage/driveloom-pois-<region hash>.db`: fertige Geofabrik-Regionalkataloge je Auswahl. Downloads und neue Importdatenbanken sind temporär; fertige Bestände sollen bei Fehlern erhalten bleiben. Auswahl allein löscht keine Katalogdatei; Löschknopf nach Abwahl und Speicherung nutzen, solange die Datei nicht von einem Import verwendet wird.
- `.storage/driveloom-ocpdb.db`: bis zu sechs komprimierte, vollständige Suchgebiets-Snapshots. Keine komplette Länder-Datenbank. Suchstandorte/Preise bis 15 Minuten, Verfügbarkeitsdaten nur kurz wiederverwenden und bei veralteten Daten als unbekannt bewerten.
- Reise-ZIP exportiert und restauriert Ordner, eigene POIs, Notizen und Dokumente in ein **leeres** Reisearchiv. Es enthält keine GPS-Historie, Hauptkonfiguration, Geofabrik-Kataloge oder HA-Einstellungen. Für alles andere HA-Backup verwenden. Live-SQLite-Dateien einschließlich WAL nicht blind während laufender Schreibvorgänge kopieren.

## Derzeitige Bedienfunktionen

1. **Fahrzeuge und Tracking:** mehrere Fahrzeuge, Analytics, Live-GPS oder Companion-Telefonposition, historische Tracks und Fahrten, GPS-Export, Wiedergabe und Kameramodi. GPS-Follow kann gewählte Basiskarte, Zoom und Heading nutzen. Die Kamera soll aktuelle valide Fahrzeugdaten verwenden.
2. **Map/POIs:** OSM, OSM+, Topo, Satellit und 3D; freie Karte oder GPS-Follow. Vorlagen speichern kombinierte allgemeine POIs (z. B. Fastfood) und Ladestationen mit unabhängigen Textfiltern. POI-Zentrum ist Fahrzeug oder Kartenmitte. Karten-Pins, Touch-Swipe/Scrollen und Pfeile erlauben die Auswahl der 1–3 sichtbaren POIs aus größeren Mengen. Doppelpfeile springen Anfang/Ende. Standtest zeigt ausgewählte POIs ohne Fahrtbewegung; GPS-Follow berücksichtigt einen zuverlässigen Heading-Korridor. Abstände sind Luftlinie, kein Straßenumweg.
3. **POI-Detail:** Zoom auf Ziel, zurück zur alten Ansicht oder Google-Maps-Navigation. Betreiber eines Ladepunkts zuerst und fett; Ort/Adresse soweit verfügbar; technische Kennung nachgeordnet. Links zu Betreiber oder Station nur bei tatsächlich vorhandener Quelle bzw. ausdrücklich gekennzeichneter Referenz.
4. **Regionaler Katalog:** Auswahl zahlreicher Geofabrik-Länder und optional deutscher Bundesländer, zeitgesteuerte Aktualisierung, Download- und separater Importfortschritt. Lange Importe können viel CPU, freien Speicher und Zeit brauchen. Die Trefferzahl auf der Karte ist ein Anzeigelimit, nicht die Gesamtzahl gespeicherter POIs.
5. **OCPDB-Ladepunkte:** optionale Quelle `OCPDB · MobiData BW (Deutschland)` neben Open Charge Map. `ocpdb.py` verwendet öffentliche `https://api.mobidata-bw.de/ocpdb/api/public/ocpi/3.0`-Daten sowie `/v1/sources`; anwendbare Tarife werden je EVSE/Stecker zugeordnet. Es gibt Betreiber, Steckertyp, Mindestleistung, bekannten bzw. maximalen eindeutigen Ad-hoc-Energiepreis, verfügbare Ladepunkte und Mindestzahl frei. Der Server filtert deutsche Stationen und paginiert mit Sicherheitsgrenze, meldet unvollständige Ergebnisse. Unbekannte oder alte Preise/Status erfüllen keine strengen Filter. Zeitgebühren getrennt kennzeichnen. Preis/Verfügbarkeit vor dem Laden prüfen.
6. **Reiseplanung:** frei verschachtelte, verschiebbare und umbenennbare Ordner mit Reisezustand, eigene POIs aus Karte/Bestand/Koordinaten, Markerfarbe und Kürzel, globale und reisespezifische Notizen, Ordnernotizen, Dokumente und Filter „alle eigenen Reise-POIs“. Recherche-POIs können anhand globaler Vorlagen eingeblendet werden. Adressen werden nach ausdrücklicher Suche über Photon gesucht; eingegebene Koordinaten oder unterstützte Google-Maps-Koordinatenlinks lokal geparst. Reiseordner sind getrennt von historischen Fahrten.
7. **Routen:** Start, Zwischenziele und Ziel; Google Maps übernimmt tatsächliches Routing und Navigation. Eine Peilung auf ein Routenziel ist kein Straßenkorridor.

## Neuer Stand v0.2.0b11: iPad-App-Wechsel

Das beobachtete Problem: In der POI-Planung wurde auf dem iPad nach einem Wechsel zu Safari und zurück das POI-Panel geschlossen und die Karte wieder auf die Fahrzeuge eingepasst. Die UI-Sichtbarkeit war nicht Teil der gespeicherten Präferenzen; ein neues Kartenelement führte beim ersten Render ein Fahrzeug-Fit aus. Die Beta speichert `poiPanelOpen` in `driveloom/preferences/set` pro HA-Benutzer und hält Panel plus tatsächliche MapLibre-Mitte/Zoom sofort im `sessionStorage` desselben Browser-Tabs. `visibilitychange`, `pagehide`, Kartenbewegung und Entfernen des Kartenelements erfassen die Ansicht. Bei der Wiederherstellung hat der Tab die aktuellere Ansicht vor asynchron gespeicherten Serverpräferenzen; `_renderFull` überspringt den ersten Fahrzeug-Fit, wenn eine Kartenposition wiederhergestellt wurde. GPS-Follow priorisiert die aktuelle Fahrzeugkamera. Panel schließen entfernt den temporären Tab-Eintrag. Ein geöffneter Popup-Inhalt wird nach komplettem Seitenneuladen nicht wieder geöffnet. Ob iPad Safari den Tab tatsächlich erhält bzw. neu erstellt, muss auf dem Gerät geprüft werden.

## Anforderungen, Grenzen, offene Ideen

- Nutzerziel: verlässliche, während der Fahrt nutzbare POI-Vorschau, schnelle Navigation, kombinierbare Vorlagen; auf iPhone/iPad gut bedienbar. Testen auch im Stand und mit verschobener Kartenmitte. Bei UI-Änderungen Safari/Companion und Browser Mode berücksichtigen.
- Reiseplanung soll langfristig mit verschachtelten Ordnern, Dokumenten und eigenen recherchierten Zielen ausgebaut werden. Die vorhandene Beta liefert den Kern, nicht alle künftigen Ideen.
- Größere und internationale Ladequellen sind ein möglicher späterer Ausbau. Die aktuelle OCPDB-Auswahl ist auf Deutschland begrenzt; die Schweiz ist ausdrücklich keine Aufgabe für dieses Release. Länderabdeckung und Preisdaten dürfen nicht aus einer bloßen API-URL hergeleitet werden.
- Keine Behauptung, alle Ad-hoc-Tarife seien lückenlos, aktuell, amtlich garantiert oder kostenlos/unlimitiert verfügbar. Beachte Quellstand, Konditionen, Zuordnung zu konkretem Stecker, Zeitgebühren und Offline-Fallback.
- Das alte obere Menü „Schnelllader voraus · manuell“ wurde in b10 entfernt. Sein Zweck wird über das untere POI-Panel, globale Vorlagen und Standtest abgedeckt. Nicht versehentlich wieder einführen.
- Ein umfassender internationaler Preisvergleich, echter Streckenkorridor, berechneter Umweg und automatisierte KI-Recherche sind **nicht** Bestandteil der aktuellen Version. Vor Erweiterung Quellen, API-Regeln und Tests konkret festlegen.

## Verifikation und Releaseablauf

Im Repository: `node --check custom_components/driveloom/frontend/driveloom-card-0.2.0b11.js`, `node tests/test_frontend.cjs`, `python -m compileall -q custom_components/driveloom tests` sowie passende Python-Tests in `tests/`. `git diff --check` ausführen. Die Frontend-Suite nutzt DOM-/MapLibre-Adapter offline und ersetzt keine echte Safari-, iPad- oder HA-Prüfung. Nicht nur Syntax testen: Zustandsübergänge, asynchrones Speichern, Marker/Layers und Filter müssen sichtbar geprüft werden.

Paketieren: Repository-Stamm mit `.github`, `custom_components`, `hacs.json`, README, Changelog, Lizenz, Release Notes, diesem Übergabetext und Tests; keine `.git`, Python-Caches, temporären Testordner oder vorherige Frontend-JS im aktuellen Verzeichnis. Danach ZIP in einen frischen Ordner entpacken, alle Dateien gegen die Quelle vergleichen, Versionsverweise und Namen erneut prüfen und die Tests nochmals **aus dem entpackten ZIP** ausführen. Nenne SHA-256 und unterscheide geprüfte Offline-Funktionen von ausstehenden Gerätetests. Ich kopiere die ZIP-Dateien selbst nach GitHub und erstelle den Beta-Tag.

---

**Auftrag an den nächsten Assistenten:** Frage nach meiner nächsten konkreten Änderung oder bearbeite den bereits genannten Auftrag. Beginne bei einem Bug mit der Reproduktion im vorhandenen Code und einem gezielten Test; liefere erst nach geprüfter Änderung ein neues Beta-Release. Erfinde weder API-Daten noch Ergebnisse einer realen Fahrt. Bewahre diese Architektur- und Releasevereinbarungen.
