# DriveLoom v0.1.4 — Drei gut lesbare POIs in Fahrtrichtung

## Änderungen

- Im GPS-Follow erscheinen bis zu drei passende POIs in Fahrtrichtung als getrennte, größere Schaltflächen. Gibt es weniger Treffer, erscheinen entsprechend weniger Zeilen.
- Betreibername beziehungsweise POI-Name und Luftdistanz sind auf dem Smartphone größer und deutlicher. Die Bestätigung und ihre Schaltflächen sind ebenfalls vergrößert.
- Alle drei Ziele stammen gemeinsam aus den geladenen, ausgewählten Kategorien und Betreiberfiltern. Die Reihenfolge folgt der aktuellen Luftdistanz innerhalb des Suchradius und Fahrtrichtungskorridors, nicht einer berechneten Straßenroute.
- Ein Tipp auf eine der Zeilen zeigt die Bestätigung genau für dieses Ziel. Erst danach öffnet „Google Maps öffnen“ die Navigation; Google Maps kann abhängig vom Gerät zuerst eine Routenvorschau anzeigen.
- Im POI-Panel startet „POI-Hinweis testen“ eine zwei Minuten lange, deutlich markierte Testansicht. So lassen sich im Stand die drei nächstgelegenen geladenen POIs samt Auswahl und Bestätigung testen. Die Testansicht ignoriert bewusst die Fahrtrichtung und endet automatisch oder über „Test beenden“.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt jetzt `driveloom-card-0.1.4.js?v=0.1.4`.

## Manuelle Veröffentlichung und Installation

Den entpackten ZIP-Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.3.js` entfernen. Den neuen GitHub-Commit als `v0.1.4` taggen, diesen Release-Text verwenden und `DriveLoom_0.1.4_GitHub_HACS.zip` selbst als Release-Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.4.js?v=0.1.4` ersetzen.

## Prüfung und Grenzen

Automatisierte Tests und Paketprüfungen laufen lokal und nach frischer ZIP-Extraktion. Ein Fahrttest auf dem iPhone bleibt eine praktische Prüfung. Die Luftdistanz berücksichtigt weder Straßenverlauf noch Zufahrt oder Verfügbarkeit einer Ladestation.
