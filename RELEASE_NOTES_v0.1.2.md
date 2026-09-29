# DriveLoom v0.1.2 — Live GPS Follow

## Änderungen

- GPS-Follow bleibt beim Wechsel zwischen OSM, OSM+, Topo, Satellit und 3D aktiv. Der gewählte Kartenstil und GPS werden gleichzeitig angezeigt.
- Das Fahrzeug bleibt bei frei gewähltem Zoom in der Kartenmitte. Neue Telefon-Fixes führen die Kamera jetzt ebenfalls nach; bei aktivem Follow wird der Telefonstatus alle fünf Sekunden abgefragt.
- Nach aufeinanderfolgenden plausiblen Positionsänderungen dreht sich die Karte in Fahrtrichtung. Bei Stillstand, GPS-Rauschen oder einem unplausiblen Sprung bleibt die letzte verlässliche Ausrichtung erhalten.
- Der GPS-Knopf schaltet Follow auch wieder aus. Bewusstes Verschieben der Karte und das Einpassen historischer Tracks beenden Follow weiterhin.
- Beide Lovelace-Cards werden über die neue Ressource `driveloom-card-0.1.2.js?v=0.1.2` geladen. Im YAML-Ressourcenmodus den bisherigen Eintrag ersetzen; im Storage-Modus aktualisiert die Integration ihn selbst.

## Installation

Das ZIP als Asset des Tags `v0.1.2` hochladen und DriveLoom über HACS aktualisieren. Danach Home Assistant neu starten. Falls die Ressourcen in YAML verwaltet werden, den JavaScript-Modulpfad auf `/driveloom/driveloom-card-0.1.2.js?v=0.1.2` ändern und die Karte neu laden.

## Prüfung und Grenzen

Die automatisierten Python- und Frontendtests sowie Syntax-, JSON- und Paketprüfungen wurden lokal durchgeführt. Ein realer Home-Assistant-Start und eine Fahrt mit iPhone/CarPlay bleiben praktische Tests. Follow reagiert auf bei Home Assistant eintreffende Positionsdaten; die mobile Standortübermittlung selbst wird von DriveLoom nicht erzwungen.
