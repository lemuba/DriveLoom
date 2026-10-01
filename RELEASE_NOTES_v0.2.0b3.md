# DriveLoom v0.2.0b3 — Beta

## Änderungen

- **PDF-Vorschau:** Die bisherige Sandbox-Sperre des eingebetteten PDF-Fensters wurde entfernt. Falls der Browser das PDF trotzdem nicht innerhalb der Karte darstellen kann, gibt es „PDF im Browser öffnen“. „Herunterladen“ bleibt eine eigene Aktion. Bilder und Text behalten ihre Vorschau; Office-Dateien zeigen Details und Download.
- **Dokumente verschieben:** In der Dokumentansicht kann ein Zielordner aus der gesamten Reiseordnerstruktur gewählt werden. DriveLoom prüft zuvor das Gesamtvolumen am Ziel. Unter einer Reise gilt deren Limit; andere Ordner nutzen das Limit ihres obersten Ordners (anfangs jeweils 100 MiB). Die gespeicherte Datei selbst wird beim Verschieben nicht erneut übertragen.
- **Eigene POI-Pins:** Die Reise-Marker werden nach dem Übernehmen eines Karten-POIs und nach einem Kartenstilwechsel erneut synchronisiert. Der ausgewählte POI erhält einen größeren Marker. Für jeden eigenen POI lassen sich eine Markerfarbe und ein Symbol aus einem oder zwei Buchstaben/Ziffern speichern; bei fehlender Auswahl verwendet DriveLoom ein Kürzel aus der Kategorie.
- **Alle Reise-POIs:** Der neue Schalter im Reise-Panel zeigt sämtliche eigenen POIs, auch noch nicht zugeordnete, und lässt sie nach dem Schließen des Panels auf der Karte stehen. POIs aus der globalen Vorlage sind dabei ausgeblendet. Ausschalten stellt die vorherige POI-Ansicht wieder her.
- **POI-Details:** Eine gültige Webadresse erhält „Webseite im Browser öffnen“. Direkt unter „Adresse“ steht nun eine editierbare Hauptnotiz. Diese Notiz und andere POI-Daten sind gemeinsam, wenn derselbe POI mehreren Ordnern zugeordnet ist; weitere Reisenotizen bleiben separat. Die Zuordnungsauswahl erklärt das deutlicher.

Die Reise-Datenbanken aus `v0.2.0b1` und `v0.2.0b2` werden weiterverwendet; eine Neuinstallation der Reisedaten ist nicht nötig. Die stabile Version `v0.1.14` bleibt unverändert.

## Manuell auf GitHub veröffentlichen

1. `DriveLoom_0.2.0b3_GitHub_HACS.zip` herunterladen und entpacken. Den **Inhalt des ZIP-Stammverzeichnisses** selbst in dein GitHub-Repository übernehmen, einschließlich `custom_components/driveloom`, `hacs.json`, README und Changelog.
2. Auf genau diesem Stand den **neuen Tag `v0.2.0b3`** anlegen, ein GitHub-Release erstellen, diese Notes als Beschreibung verwenden und **„Set as a pre-release“** aktivieren. Das ZIP kann zusätzlich als Release Asset hochgeladen werden.
3. In HACS Beta-Versionen für DriveLoom zulassen und das neue Release installieren. Bei manueller Installation `custom_components/driveloom` in die Home-Assistant-Konfiguration kopieren. Home Assistant neu starten und die Karte bei Bedarf im Browser neu laden. Bei YAML-Ressourcen die URL auf `/driveloom/driveloom-card-0.2.0b3.js?v=0.2.0b3` umstellen.

## Praxistest

- PDF im Browser und auf iPhone/iPad öffnen; Vorschau und „PDF im Browser öffnen“ ausprobieren.
- Ein Dokument zwischen zwei Reisen und in einen normalen Ordner verschieben; bei zu kleinem Zielvolumen muss die Verschiebung abgelehnt werden.
- Einen bestehenden Karten-POI zur Reise hinzufügen und seinen Pin prüfen. Symbol und Farbe speichern, danach Kartenstil und Ordner wechseln.
- „Alle eigenen Reise-POIs“ einschalten, Reise-Panel schließen und wieder öffnen; globale Vorlagen-POIs müssen währenddessen ausgeblendet bleiben und nach dem Ausschalten zurückkehren.
- Webseite und Hauptnotiz eines POIs speichern und die gemeinsame Zuordnung zu einem zweiten Ordner prüfen.

Offline-Tests und zwei unabhängige Prüfungen des vollständigen ZIPs sind vor der Bereitstellung durchgeführt worden. Browser- und Home-Assistant-Tests auf deinem System bleiben für diese Beta erforderlich.
