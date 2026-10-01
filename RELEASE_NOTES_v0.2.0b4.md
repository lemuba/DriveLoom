# DriveLoom v0.2.0b4 — Beta

## Korrektur

- Eigene Reise-POIs erscheinen nun als sichtbare Kartenmarker mit ihrer gespeicherten Farbe und dem Kürzel aus 1–2 Zeichen. Der Klick auf den Pin öffnet den zugehörigen POI und zentriert ihn auf der Karte.
- Die Marker werden beim Wechsel des Reiseordners und beim Ausblenden der Reise-POIs aktualisiert. Nach einem Neuaufbau der Karte werden sie wieder angelegt. Die bisherige Kartenebene bleibt für Suchtreffer und als technischer Ersatz, falls DOM-Marker nicht verfügbar sind.
- Der Kartenfokus kommt auch dann ohne JavaScript-Fehler aus, wenn die Kartenfläche während eines Neuaufbaus noch nicht verfügbar ist.

Die vorhandenen Reise-POIs, Farben, Dokumente und SQLite-Daten bleiben erhalten. `v0.1.14` bleibt der unveränderte stabile Release.

## Manuell auf GitHub veröffentlichen

1. `DriveLoom_0.2.0b4_GitHub_HACS.zip` herunterladen und entpacken. Den **Inhalt des ZIP-Stammverzeichnisses** in dein GitHub-Repository kopieren, einschließlich `custom_components/driveloom`, `hacs.json`, README, Changelog und dieser Release Notes. Die bisherige Datei `custom_components/driveloom/frontend/driveloom-card-0.2.0b3.js` im Repository entfernen; der neue Stand enthält nur `driveloom-card-0.2.0b4.js`.
2. Für diesen Stand einen **neuen Tag `v0.2.0b4`** und ein GitHub-Release anlegen, diese Notes als Beschreibung verwenden und **„Set as a pre-release“** aktivieren. Das ZIP kann zusätzlich als Release Asset hochgeladen werden.
3. In HACS die Beta-Version installieren oder die entpackten Dateien manuell nach Home Assistant übernehmen. Home Assistant neu starten und die Karte im Browser neu laden. Bei YAML-Ressourcen die URL auf `/driveloom/driveloom-card-0.2.0b4.js?v=0.2.0b4` umstellen.

## Praxistest

- Im Reisearchiv einen eigenen POI mit Farbe und Kürzel wählen. Der Pin soll an der gespeicherten Position erscheinen und beim Antippen wieder zu diesem POI führen.
- Den Ordner und den Kartenstil wechseln; anschließend „Alle eigenen Reise-POIs auf Karte zeigen“ ein- und ausschalten. Pins sollen passend erscheinen beziehungsweise verschwinden.
- Einen Pin auf iPhone und iPad ansehen und antippen; Browserlayout und die konkrete Home-Assistant-Umgebung können Offline-Tests nicht vollständig nachbilden.

Die Frontend- und Backend-Tests sowie zwei Prüfungen des entpackten ZIP-Inhalts wurden vor der Bereitstellung durchgeführt.
