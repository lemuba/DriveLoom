# DriveLoom v0.2.0b2 — Beta

## Neu und verbessert

- **Reiseordner wie im Datei-Explorer:** Per Tippen oder Klick öffnen, Zweige aufklappen und über die Pfadleiste zurückgehen. Auf Desktop lassen sich Ordner auf andere Ordner ziehen; auf Touch-Geräten gibt es weiterhin die Auswahl „In Ordner verschieben“.
- **Eigene Reise-POIs auf der Karte:** „Nur Reise-POIs“ zeigt die eigenen Ziele des gewählten Ordners, optional mit Unterordnern. Die oberste Ebene zeigt alle zugeordneten eigenen POIs. „Recherche-POIs“ stellt die globalen POI-Vorlagen für die Reiseplanung bereit. Ein eigener POI lässt sich antippen, hervorheben und mit dem einstellbaren Vorlagen-Detailzoom auf der Karte betrachten; „Zurück zur Karte“ stellt die vorherige Kameraposition wieder her.
- **Kartenpunkt per langem Druck:** Ein langer Druck auf die Karte legt einen eigenen POI im gewählten Ordner an. Eine Wischbewegung bricht den Druck ab. Die bisherige Schaltfläche zur Auswahl eines Kartenpunkts bleibt erhalten.
- **Ortssuche und Google-Maps-Koordinaten:** Ort oder Adresse suchen; Suchergebnisse öffnen die Karte und können anschließend als eigener POI gespeichert werden. Direkte Koordinaten und Google-Maps-Links mit eingebetteten Koordinaten funktionieren ohne Ortsanfrage. Kurzlinks ohne Koordinaten lassen sich nicht auflösen. Die ausdrücklich gestartete Ortssuche verwendet Photon (komoot) über Home Assistant; es gibt keine automatische Suche während der Eingabe.
- **Dokumente zuerst ansehen:** Ein Klick öffnet Details und bei PDF, gängigen Bildern oder Text eine Vorschau. Das Herunterladen ist eine eigene Aktion. Für Vorschauen über 30 MiB ist eine weitere Bestätigung erforderlich; Office-Dateien und sonstige Formate zeigen Details und können separat heruntergeladen werden.
- Mobil bleibt die Karte oberhalb des Reise-Panels sichtbar, während Ordner und Dokumente im Panel scrollbar sind.

Die stabile Version `v0.1.14` bleibt unverändert. Dieses Release erweitert `v0.2.0b1`; die Reise-Datenbanken und bisherigen Archive werden weiter verwendet.

## Manuelle Veröffentlichung und Installation

1. `DriveLoom_0.2.0b2_GitHub_HACS.zip` herunterladen und entpacken. **Den Inhalt** des ZIP-Stammverzeichnisses in dein GitHub-Repository hochladen, einschließlich `custom_components/driveloom`, `hacs.json`, README und Changelog.
2. Auf GitHub einen **neuen Tag `v0.2.0b2`** auf genau diesem Stand anlegen. Diese Datei als Release-Beschreibung verwenden und **„Set as a pre-release“** aktivieren. Das ZIP kann zusätzlich als Release Asset hochgeladen werden.
3. In HACS Beta-Versionen dieser Integration zulassen und das neue Release wählen. Bei manueller Installation `custom_components/driveloom` in die Home-Assistant-Konfiguration kopieren. Home Assistant neu starten; falls noch die alte Kartenfassung erscheint, Browser-Cache aktualisieren. Bei YAML-Ressourcen die URL auf `/driveloom/driveloom-card-0.2.0b2.js?v=0.2.0b2` ändern.

## Zum Testen

- Auf iPhone/iPad und Desktop eine Reise mit Unterordner öffnen, zwischen eigener und Recherche-Ansicht wechseln und eine globale POI-Vorlage laden.
- Einen Kartenpunkt kurz über die Schaltfläche und einen anderen per langem Druck speichern. POI antippen, Zoom und Rückkehr prüfen.
- `59.437, 24.753`, einen Google-Maps-Link mit eingebetteten Koordinaten und eine Adresse suchen. Nur ausdrücklich gespeicherte Treffer dürfen im Archiv erscheinen.
- PDF und Bild öffnen: zunächst Vorschau, Download erst mit eigenem Knopf. Eine Office-Datei soll Details und einen Downloadknopf zeigen.

Offline wurden Python- und Frontend-Verhaltenstests, Syntax, Versionsreferenzen und das vollständige ZIP zweimal geprüft. Ein echter Home-Assistant- und iOS-Test ist weiterhin erforderlich.
