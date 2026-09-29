# DriveLoom v0.1.8 — POI-Bedienung per Touch

## Änderungen

- Das rechte POI-Einstellpanel kann auf dem iPad und auf schmalen Karten vollständig nach oben und unten gescrollt werden. Bei einer Aktualisierung bleibt die Scrollposition erhalten, sodass die unteren Einstellungen erreichbar bleiben.
- In der POI-Hinweiskachel blättert ein Wischen **nach oben** zu weiter entfernten, ein Wischen **nach unten** zu näheren POIs. Mausrad und Trackpad funktionieren ebenfalls direkt über der Liste.
- Ein kompakter Touch-Schieberegler unter den Pfeilen erlaubt das Springen zu einer Position innerhalb aller geladenen Treffer. Einzel- und Doppelpfeile bleiben nutzbar.
- Weiterhin werden nur die eingestellten 1–3 sichtbaren POI-Zeilen erzeugt; auch bei 500 geladenen Treffern muss die Karte keine lange HTML-Liste darstellen.
- Die gemeinsame Kartenressource für beide Lovelace-Cards heißt jetzt `driveloom-card-0.1.8.js?v=0.1.8`.

## Manuelle Veröffentlichung und Installation

Den entpackten ZIP-Inhalt ins GitHub-Repository übernehmen und die alte Frontend-Datei `driveloom-card-0.1.7.js` entfernen. Den neuen GitHub-Commit als `v0.1.8` taggen, diesen Release-Text verwenden und `DriveLoom_0.1.8_GitHub_HACS.zip` selbst als Release-Asset hochladen. Nach dem HACS-Update Home Assistant neu starten. Bei YAML-Ressourcen den alten JavaScript-Eintrag durch `/driveloom/driveloom-card-0.1.8.js?v=0.1.8` ersetzen.

## Prüfung und Grenzen

Automatisierte Verhaltens-, Syntax- und Paketprüfungen laufen lokal und nach frischer ZIP-Extraktion. Das reale Scrollverhalten in Safari auf iPad und iPhone ist anschließend praktisch zu prüfen. Der Schieberegler und die Wischgesten navigieren durch bereits geladene, gefilterte POIs im eingestellten Umkreis; sie lösen keine zusätzliche Suche aus.
