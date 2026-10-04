# Changelog

## 0.2.0 — Aktuelles Release

- Automatischer GPS-Start wahlweise über eine vorhandene CarPlay-/WLAN-SSID oder eine Home-Assistant-Entität `binary_sensor.*`. Bei Binärsensoren startet `on` die Fahrt; `off`, `unknown` und `unavailable` gelten als getrennt und nutzen die vorhandene Pausen- und Abschaltlogik.
- Bestehende SSID-Regeln bleiben ohne Konvertierung lesbar und wirksam. Die GPS-Verwaltung zeigt den gewählten Auslöser mit den passenden Eingabefeldern.
- POI-Panel, Kartenmitte und Zoom bleiben bei einem App-Wechsel bzw. Karten-Neuaufbau erhalten; GPS-Follow steuert weiterhin seine eigene Fahrzeugkamera.
- Das Repository-Paket enthält nur aktuelle Release-Hinweise und die versionierte Karte `driveloom-card-0.2.0.js`.

Die vollständige Funktionsübersicht und die bebilderten Installationshinweise in der README werden in einem gesonderten Schritt überarbeitet.
