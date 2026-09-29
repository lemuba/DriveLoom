# DriveLoom v0.1.6 — POI-Vorlagen und weitere Ziele im GPS-Follow

## Änderungen

- Die Hinweiskachel auf der Karte bietet bei gespeicherten globalen POI-Vorlagen eine dezente Auswahl direkt neben der Überschrift. Die Vorlagenfilter und der Radius werden übernommen; im GPS-Follow dient weiterhin das aktuelle Fahrzeug als Suchzentrum.
- Beim Wechsel zeigt die Kachel „POIs werden geladen …“, bevor sie Treffer der neuen Vorlage anbietet. Bei einem endgültigen Ladefehler erscheint eine Fehlermeldung statt möglicherweise veralteter Navigationsziele.
- Sind mehr POIs geladen als die eingestellte Anzahl 1–3, verschiebt **↑** die sichtbare Gruppe um einen weiter entfernten POI und **↓** um einen näheren. Ein Zähler zeigt die Position innerhalb der geladenen, passenden Treffer.
- Neue GPS-Punkte halten die gewählte Gruppe möglichst am bisherigen ersten sichtbaren POI fest. Wenn er passiert wurde, rückt der nächste noch passende nach. Ein Vorlagenwechsel beginnt wieder bei den nächsten Zielen.
- Die Zielbestätigung bleibt an den tatsächlich angetippten POI gebunden. Die Reihenfolge verwendet Luftdistanz innerhalb des Fahrtrichtungskorridors, nicht die Straßenroute.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt jetzt `driveloom-card-0.1.6.js?v=0.1.6`.

## Manuelle Veröffentlichung und Installation

Den entpackten ZIP-Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.5.js` entfernen. Den neuen GitHub-Commit als `v0.1.6` taggen, diesen Release-Text verwenden und `DriveLoom_0.1.6_GitHub_HACS.zip` selbst als Release-Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.6.js?v=0.1.6` ersetzen.

## Prüfung und Grenzen

Automatisierte Tests und Paketprüfungen laufen lokal und nach frischer ZIP-Extraktion. Das Layout und die Bedienung auf dem iPhone während einer Fahrt bleiben praktische Prüfungen. Die Pfeile blättern nur durch bereits geladene und gefilterte POIs im gewählten Radius; die Luftdistanz berücksichtigt weder Straßenverlauf noch Zufahrt oder Verfügbarkeit.
