# DriveLoom

**DriveLoom verbindet Fahrzeugdaten aus Home Assistant mit Verbrauchsanalyse, GPS-Fahrten und einer interaktiven Karte.** Auf derselben Karte kannst du Ladestationen und andere POIs recherchieren, Ziele planen und eigene Reisen mit Notizen und Dokumenten archivieren. Die Integration verwaltet ihre Daten in Home Assistant und funktioniert unabhängig von Cardata Analytics; dessen Daten werden weder gelesen noch übernommen.

Die aktuelle Version ist **0.2.0**. DriveLoom enthält eine Fahrzeug- und Verbrauchsübersicht sowie eine Fahrzeugkarte für GPS, POIs, Routen und Reisen.

[☕ DriveLoom auf Ko-fi unterstützen](https://ko-fi.com/lemuba20013)

<img src="docs/screenshots/analytics-overview.jpg" alt="DriveLoom Fahrzeugübersicht mit Vergleichszeitraum und Verbrauchswerten" width="580">

## Installation

### Voraussetzungen

- Home Assistant **2026.1.0 oder neuer**.
- Vorhandene Home-Assistant-Sensoren für **Ladezustand (SoC)** und **Kilometerstand** je Fahrzeug. Die nutzbare Batteriekapazität wird ebenfalls benötigt: als Sensor bei den BMW-Profilen oder als Sensor beziehungsweise fester Wert beim generischen BEV.
- Optional: Reichweite, SoH und GPS-Breitengrad/-Längengrad. Die beiden GPS-Sensoren müssen gemeinsam konfiguriert werden.
- Für **Open Charge Map** ist bei aktivierter Quelle ein eigener API-Schlüssel erforderlich. Der Schlüssel bleibt im Home-Assistant-Backend. **OCPDB · MobiData BW** benötigt keinen Open-Charge-Map-Schlüssel.

### HACS als benutzerdefiniertes Repository

1. **HACS** öffnen und im Menü mit den drei Punkten **Benutzerdefinierte Repositories** wählen.
2. `https://github.com/lemuba/DriveLoom` eintragen, als Typ **Integration** wählen und hinzufügen.
3. **DriveLoom** in HACS öffnen und die aktuelle Version herunterladen.
4. **Home Assistant neu starten**. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **DriveLoom** suchen und ein Fahrzeug einrichten.

HACS verwaltet die Integrationsdateien. Im Lovelace-Storage-Modus registriert DriveLoom seine Dashboard-Ressource beim Start automatisch. Für den YAML-Ressourcenmodus ist zusätzlich der unten genannte Eintrag nötig. Allgemeine Hinweise: [HACS – Custom Repositories](https://www.hacs.dev/docs/faq/custom_repositories/).

### Manuell installieren

1. Den vollständigen Ordner `custom_components/driveloom` nach `<HA-Konfigurationsverzeichnis>/custom_components/driveloom` kopieren. Die Unterordner einschließlich `frontend/`, `brand/` und `translations/` erhalten.
2. Bei einem Update alle Dateien der neuen Version übernehmen. Alte versionierte `driveloom-card-*.js` im Zielordner entfernen, sofern sie nicht mehr zur installierten Version gehören.
3. Home Assistant neu starten und **DriveLoom** wie oben unter **Einstellungen → Geräte & Dienste** hinzufügen.

### Fahrzeug und Dashboard einrichten

Zunächst **BMW i3 120 Ah**, **BMW iX1** oder **BEV** wählen. Danach Namen, SoC-Sensor und Kilometerstand-Sensor zuordnen. Bei den BMW-Profilen den Sensor für die **nutzbare Gesamtkapazität** der Hochvoltbatterie angeben, nicht den momentanen Energieinhalt. Für BEV kann alternativ eine feste nutzbare Kapazität in kWh eingetragen werden. Reichweite, SoH und GPS-Sensoren sind abhängig vom Fahrzeugprofil optional. Weitere Fahrzeuge werden über **Gerät hinzufügen** eingerichtet; vorhandene lassen sich später neu konfigurieren.

<img src="docs/screenshots/integration-devices.jpg" alt="DriveLoom als Home-Assistant-Integration mit mehreren Fahrzeugen" width="580">

<details><summary>Beispiel: Zuordnung der Fahrzeugsensoren</summary>

<img src="docs/screenshots/vehicle-setup.jpg" alt="Einrichtungsformular für SoC, Kilometerstand, Kapazität und optionale GPS-Sensoren" width="430">

</details>

Füge anschließend in einem Dashboard eine **Manuelle Karte** mit einem der folgenden Inhalte hinzu:

```yaml
type: custom:driveloom-card
```

```yaml
type: custom:driveloom-map-card
```

Bei Lovelace im **YAML-Ressourcenmodus** zusätzlich diese JavaScript-Modulressource eintragen:

```yaml
resources:
  - url: /driveloom/driveloom-card-0.2.0.js?v=0.2.0
    type: module
```

Bei einem Update die Dashboard-Seite neu laden. Falls noch eine ältere Version angezeigt wird, Browser- oder App-Cache sowie den Ressourcenpfad prüfen.

## Funktionsumfang

### Fahrzeugübersicht und Verbrauch

Die Analysekarte zeigt Fahrzeugzustand, SoC, Reichweite, Kilometerstand und Kapazität sowie Verbrauch und Fahrleistung für heute, Woche, Monat, Jahr und einen selbst gewählten Zeitraum. Ein gemeinsamer Datumsbereich erlaubt den Vergleich mehrerer Fahrzeuge. Fahrten- und Verbrauchsanalysen verwenden die von DriveLoom gespeicherten Daten; fehlende Werte werden nicht als gemessene Nullen ausgegeben. Werkzeuge zur Prüfung und Reparatur der SoC-Daten sind in der Übersicht erreichbar.

### Fahrzeugkarte und Kartensteuerung

Die Karte zeigt mehrere Fahrzeuge mit ein- und ausblendbaren Markern und, soweit Daten vorhanden sind, deren Reichweite. Zur Wahl stehen **OSM, OSM+, Topo, Satellit und 3D**. In 3D lassen sich unter anderem Neigung, Drehung und Geländehöhe einstellen. **GPS-Follow** hält das gewählte Fahrzeug im Blick und kann nach zuverlässigen aufeinanderfolgenden Positionspunkten die Fahrtrichtung nach oben drehen. Eine Fahransicht blendet die obere Bedienleiste aus und gibt der Karte mehr Platz.

<img src="docs/screenshots/vehicle-map.jpg" alt="Fahrzeugkarte mit zwei Fahrzeugen, Reichweiten und POI-Markern" width="620">

Kartenposition, Zoom und ein offenes POI-Panel werden nach einem App-Wechsel oder einem Neuaufbau der Karte wiederhergestellt. Bei aktivem GPS-Follow hat die Fahrzeugkamera Vorrang. Ein geöffnetes POI-Popup wird nach vollständigem Neuladen nicht selbstständig wieder geöffnet.

### GPS-Aufzeichnung und Fahrten

Unter **Tracking/GPS-Historie** kannst du die Aufzeichnung pro Fahrzeug einschalten, Zeiträume und Darstellungen wählen, Fahrten in Ordner einordnen und Tracks auf der Karte betrachten. Die Ansicht bietet unter anderem farbige Geschwindigkeitsabschnitte, Legende, Fahrtenauswahl, GPX-Export, Wiedergabe und einen manuellen Import älterer GPS-Daten aus dem Home-Assistant-Recorder. Fahrten lassen sich einzeln oder gesammelt bearbeiten.

Neben den konfigurierten Fahrzeugsensoren sind **externe GPS-Quellen** möglich, etwa eine Position aus der iPhone-Companion-App. Fahrten können damit manuell gestartet werden. Pro Fahrzeug kann alternativ ein automatischer Auslöser verwendet werden:

- ein vorhandener Sensor mit einer bestimmten WLAN-/CarPlay-**SSID**; oder
- eine vorhandene Home-Assistant-Entität `binary_sensor.*` mit `on` für verbunden und `off` für getrennt.

Bei Unterbrechung wird die automatische Fahrt pausiert; nach Wiederverbindung kann sie fortgesetzt werden. Nach längerem Getrenntsein endet sie. Ein unbekannter oder nicht verfügbarer Binärsensor zählt als getrennt. Optional kann DriveLoom während der aktiven Fahrt Standortaktualisierungen der iPhone-Companion-App anfordern. DriveLoom **erzeugt den Binärsensor nicht selbst**. Bereits gespeicherte SSID-Regeln bleiben nutzbar.

<img src="docs/screenshots/gps-settings.jpg" alt="GPS-Historie mit externer iPhone-Quelle und automatischem Start per SSID oder Binärsensor" width="620">

<details><summary>Weitere Ansicht: aufgezeichnete Strecke und Fahrtenliste</summary>

<img src="docs/screenshots/gps-history.jpg" alt="GPS-Historie mit Track, Geschwindigkeitslegende, GPX und Fahrtenliste" width="620">

</details>

### POI-Suche, Filter und Vorlagen

Im POI-Panel kannst du Kategorien, Suchbegriffe für allgemeine POIs und getrennte Filter für Ladestationen kombinieren. Als Suchzentrum dienen das **aktuelle Fahrzeug** oder die **Kartenmitte**. Filter und Suchradius lassen sich in globalen POI-Vorlagen speichern. POI-Marker werden auf der Karte zusammengefasst und bei näherem Zoom einzeln sichtbar.

<img src="docs/screenshots/poi-filters.png" alt="POI-Panel mit Kategorien, allgemeiner Suche und getrennten Ladestationsfiltern" width="620">

<details><summary>Vorlagen auf dem Smartphone wählen</summary>

<img src="docs/screenshots/poi-presets.png" alt="Auswahl gespeicherter POI-Vorlagen über der mobilen Karte" width="290">

</details>

Mit **GPS-Follow** zeigt eine Kachel auf Wunsch **ein bis drei vorausliegende POIs** aus den geladenen und gefilterten Ergebnissen. Eine Vorlage kann direkt in der Kachel gewechselt werden. Pfeile, Doppelpfeile, Wischen, Mausrad und ein Positionsregler blättern durch weitere Treffer. Ein Tipp auf einen POI zentriert ihn beim einstellbaren Detailzoom; danach kannst du zur Fahrzeugansicht zurückkehren oder die Navigation an Google Maps übergeben. Der **POI-Hinweis-Test** zeigt die Auswahl auch im Stand. Die angezeigten Entfernungen sind Luftlinien, keine Straßenentfernungen.

<img src="docs/screenshots/poi-ahead.png" alt="Zwei POIs in Fahrtrichtung mit Betreiber, Ort und Entfernung auf dem iPhone" width="290">

<details><summary>Weitere mobile Ansichten: Vorlagenwechsel und POI-Vorschau</summary>

<img src="docs/screenshots/poi-ahead-presets.png" alt="Vorlagenauswahl innerhalb der POI-Kachel im Fahrmodus" width="290">
<img src="docs/screenshots/poi-preview.png" alt="POI-Detailvorschau mit Preis und Rückkehr zum Fahrzeug" width="290">

</details>

### Ladestationen, Preise und Verfügbarkeit

Für Ladepunkte kannst du zwischen **Open Charge Map** und **OCPDB · MobiData BW (Deutschland)** wählen. Je nach Quelle stehen Betreiber, Steckertyp, Mindestleistung, bekannter Ad-hoc-Preis, Höchstpreis pro kWh und die Mindestzahl freier Ladepunkte als Filter bereit. Diese Einstellungen können Teil einer globalen POI-Vorlage sein und werden auch für POIs in GPS-Follow verwendet.

<img src="docs/screenshots/charging-source.png" alt="Wahl zwischen Open Charge Map und OCPDB als Ladepunktquelle" width="620">

OCPDB-Preise zeigt DriveLoom nur an, wenn ein lesbarer Tarif dem betreffenden Stecker und Ladepunkt zugeordnet werden kann. Zusätzliche Zeitgebühren werden gesondert gekennzeichnet. Veraltete oder fehlende Statusmeldungen zählen als **unbekannt** und nicht als frei. Ein Ladepunkt-Popup stellt verfügbare Betreiber- und Stationslinks getrennt dar. **Preis, Status und weitere Gebühren vor dem Laden beim Betreiber oder am Ladepunkt prüfen.**

<img src="docs/screenshots/charging-details.png" alt="Ladepunktdetails auf dem iPhone mit Leistung, Ad-hoc-Preis, Belegung und Navigation" width="290">

### Regionaler POI-Katalog

Über **Points of Interest → Regionaler POI-Katalog** können Administratoren Länder und optional deutsche Bundesländer für einen lokalen OSM-POI-Katalog wählen. DriveLoom lädt regionale Geofabrik-PBF-Auszüge, importiert sie nacheinander in eigene SQLite-Dateien und aktualisiert sie zu einer eingestellten Uhrzeit im Abstand von **1 bis 30 Tagen**. Der Download zeigt übertragene Bytes und, falls bekannt, einen Fortschrittsbalken; die anschließende Datenbank-Importphase wird getrennt angezeigt. Fertige Kataloge bleiben während einer fehlgeschlagenen Aktualisierung erhalten.

Ausgewählte Regionen werden für Fahrzeugnähe und sichtbaren Kartenausschnitt abgefragt. Die einstellbare Obergrenze von **500 bis 10.000 Treffern pro Kartenabfrage** begrenzt die Darstellung, nicht den gespeicherten Katalog. Große Länder benötigen entsprechend Downloadzeit, Speicherplatz und Importzeit. Ein abgewählter Katalog kann in **Gespeicherte Kataloge** gezielt gelöscht werden. Der OSM-Katalog enthält keine Live-Belegung oder gesicherten aktuellen Ladepreise.

### Routen und Ziele

Die Routenansicht erlaubt einen Startpunkt vom Fahrzeug, vom Smartphone oder einem gewählten Ort, ein Ziel und Zwischenziele. Orte lassen sich suchen und globale Routenvorlagen speichern. Punkte auf der Karte oder POIs können als Start, Zwischenziel oder Ziel übernommen werden; für die eigentliche Navigation gibt es die Übergabe an eine externe Karten-App. Der POI-Standtest kann sich auf die Richtung zum vorhandenen Routenziel beziehen. Ein angezeigter POI „voraus“ ist dadurch **nicht automatisch entlang einer berechneten Straßenroute** geprüft.

<img src="docs/screenshots/route-planner.png" alt="Routenplanung mit Fahrzeugstart, Zwischenziel, Ziel und 3D-Kartenansicht" width="620">

### Reisen, eigene POIs und Dokumente

Unter **Reisen** legst du beliebig verschachtelte Ordner und Reiseordner an. Ordner können umbenannt, verschoben und mit Notizen versehen werden. Die Ordneransicht bietet Baum, Breadcrumbs und Bedienung per Maus oder Touch. Eigene Reise-POIs können aus bestehenden Karten-POIs, einer beliebigen Kartenposition, einer Orts-/Adresssuche oder eingefügten Koordinaten entstehen. Name, Adresse, Webseite, Farbe, Markerkürzel und Notizen sind bearbeitbar. Ein eigener POI kann mehreren Ordnern zugeordnet sein.

Du kannst nur die POIs eines Ordners samt optionalen Unterordnern oder **alle eigenen Reise-POIs** auf der Karte anzeigen. Bei der Ansicht aller eigenen POIs werden globale Vorlagen-POIs vorübergehend ausgeblendet. Für die Recherche innerhalb der Reiseansicht sind globale POI-Vorlagen ebenfalls verfügbar.

PDFs, Bilder, Office-Dateien und weitere Dokumente können in Ordner geladen und später verschoben werden. PDF, gängige Bilder und Text können je nach Browser zunächst angesehen werden; **Download ist eine gesonderte Aktion**. Office-Dateien benötigen für die Anzeige gegebenenfalls eine passende externe App. Der anfängliche Speicherrahmen beträgt **100 MiB pro Reise beziehungsweise oberstem Ordner** und ist anpassbar; es gibt keine gesonderte Größenoption pro Dokument. Reiseordner, eigene POIs, Notizen und Dokumente lassen sich als ZIP exportieren und in ein **leeres** Reisearchiv zurückspielen.

Die Suche versteht direkte Koordinaten wie `59.437, 24.753` und Google-Maps-Links mit eingebetteten Koordinaten. Eine ausdrücklich gestartete Orts-/Adresssuche verwendet den öffentlichen Photon-Dienst. Kurze Weiterleitungslinks ohne enthaltene Koordinaten werden nicht aufgelöst.

<img src="docs/screenshots/travel-archive.png" alt="Reiseplanung mit Ordnerbaum, eigenen POIs, Suche und Kartenansicht" width="620">

## Datenhaltung, externe Dienste und Sicherung

| Daten | Ablage und Hinweise |
| --- | --- |
| Fahrzeuge, Analysen, GPS-Punkte, Fahrten, Reise-Metadaten und Kartenpräferenzen | `<HA-Konfiguration>/.storage/driveloom.db` |
| Regionale OSM-Kataloge | Eigene `.storage/driveloom-pois-<Region>.db`-Dateien; ein kompletter Katalog kann nach Abwahl gelöscht werden |
| Hochgeladene Dokumentinhalte | `.storage/driveloom-documents.db`; Ordnerbeziehungen und Metadaten liegen in `driveloom.db` |
| OCPDB-Suchcache | `.storage/driveloom-ocpdb.db`; Belegungsdaten werden kürzer als Standort-/Tarifdaten verwendet |
| Home-Assistant-Konfiguration und Recorder | Werden von Home Assistant verwaltet und sind **nicht** Teil eines DriveLoom-Reise-ZIP-Exports |

Die allgemeine POI-Live-Suche nutzt OpenStreetMap-Daten, der regionale Katalog [Geofabrik](https://download.geofabrik.de/) und Ladestationen je nach Auswahl [Open Charge Map](https://openchargemap.org/) oder [MobiData BW/OCPDB](https://mobidata-bw.de/dataset/e-ladesaulen). Kartenstile und Kacheln können externe Kartendienste nutzen. Google Maps wird erst bei einer entsprechenden Navigation geöffnet. Eine ausdrücklich gestartete Adresssuche im Reisearchiv sendet den Suchbegriff an Photon; direkt eingegebene Koordinaten bleiben in Home Assistant. DriveLoom benötigt keine Gemini- oder Tavily-KI.

Die Reise-ZIP-Sicherung enthält **keine** Fahrzeugtracks, regionalen Kataloge und HA-Einstellungen. Für die gesamte Installation weiterhin Home-Assistant-Backups verwenden. Eine laufende SQLite-Datei nicht einzeln kopieren: Schreibvorgänge können noch in SQLite-WAL-Dateien stehen.

## Projekt unterstützen

Wenn dir DriveLoom gefällt, kannst du die Weiterentwicklung freiwillig über [Ko-fi unterstützen](https://ko-fi.com/lemuba20013). DriveLoom ist auch ohne Spende nutzbar.

## Lizenz und Mitwirkung

Siehe [LICENSE](LICENSE). Fehlerberichte und konkrete Verbesserungsvorschläge sind unter [GitHub Issues](https://github.com/lemuba/DriveLoom/issues) willkommen.
