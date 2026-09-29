# DriveLoom

DriveLoom is an independent Home Assistant integration for vehicle analytics, GPS tracks, trips and map views. DriveLoom starts with an empty database and can run beside Cardata Analytics. It does **not** read or migrate data from Cardata Analytics.

## Installation

Copy `custom_components/driveloom` to the matching folder below your Home Assistant configuration directory, restart Home Assistant and add **DriveLoom** through **Settings → Devices & services → Add integration**. Configure each vehicle with its source entities. Home Assistant 2026.1.0 or newer is required. This repository also includes `hacs.json` for HACS custom-repository installation.

The integration registers its dashboard card as a Lovelace resource automatically when Lovelace uses storage mode. Add `custom:driveloom-card` for the analytics overview or `custom:driveloom-map-card` for the map. In YAML resource mode, replace the old resource with `/driveloom/driveloom-card-0.1.13.js?v=0.1.13` as a JavaScript module.

On the map, GPS toggles live follow independently of OSM, OSM+, Topo, Satellite and 3D. Choose a style or zoom while following; a deliberate drag or another fit/track action exits live follow. With successive reliable position fixes, the map turns to keep the direction of travel at the top. The live camera uses the vehicle's current position, including a configured phone source; historical track markers do not control the camera.

With POIs selected, live follow can show up to three nearest loaded, filtered POIs ahead of the vehicle and their straight-line distances in larger mobile-friendly rows. If fewer match, fewer rows are shown. The POI panel has a switch for these suggestions. Multiple selected charging networks (such as IONITY, EnBW and Tesla) are treated as alternatives. Tap any destination, then confirm its Google Maps navigation link. The straight-line distance does not represent the road route, and live suggestions require a recent reliable movement heading. To try the same selection and confirmation UI while parked, tap **Test POI suggestion** in the POI panel. The two-minute preview uses the chosen number of nearest loaded POIs around the vehicle without a direction filter and is explicitly labeled as a preview.

The POI panel saves how many suggestions appear at once (1, 2 or 3), including in the stationary preview. On a phone the suggestion sits closer to the bottom edge. Tap the car button on the map to enter driving view: the title and both upper control rows disappear while the map grows to use their space. The visible map button restores the controls. GPS follow, zoom and the chosen basemap remain active.

When global POI presets exist, a compact selector in the suggestion card can switch between them without leaving GPS follow. Selecting a preset loads its saved filters and radius around the current vehicle; the card shows a loading state until matching data arrives. If more POIs are loaded than the configured visible count, the upward arrow advances one farther result and the downward arrow returns one nearer result. The visible window stays anchored to its first surviving POI as positions update, and resets when a different preset is chosen. Results are ordered by straight-line distance within the heading corridor, not by travel distance along roads.

The double arrows jump directly to the farthest or nearest visible group. Tapping a suggestion opens a compact POI detail card and centers the map on the destination at the selected detail zoom (12–20, saved with global POI presets). GPS positions and POIs continue to update while the camera stays on the POI. Use **Back to vehicle** to restore the previous follow zoom and driving direction, or **Open Google Maps** to navigate. The stationary test preview returns to its earlier map position.

The POI settings panel scrolls vertically on tablets and phones. In the map suggestion, swipe the POI rows to browse farther or nearer places, use a trackpad or mouse wheel, or drag the compact position slider below the arrows. The card still renders only the configured 1–3 rows at a time, including when hundreds of places are loaded.

### Regional POI catalogue

Open **Points of Interest → Regionaler POI-Katalog**, select any available countries (and optionally German federal states), choose the local Home Assistant hour and refresh interval (1–30 days), then save. An administrator must configure the shared catalogue. The first import starts automatically. The panel shows the count, last successful update and errors for each selection; refresh all or one country manually. Country options come from Geofabrik's index and require access to that service on first use. If the index fails to load, the panel explains the failure and provides **Weitere Länder laden** to retry.

Below the import status, **Gespeicherte Kataloge** lists complete local region databases and their sizes, including deselected countries. Deselect and save a country first; once imports have finished, confirm **Löschen** beside that country to reclaim its catalogue file. This action is limited to administrators and never deletes `driveloom.db`. Re-selecting the country later requires another download and import.

The catalogue downloads a Geofabrik OpenStreetMap PBF extract for each selection (Germany is several GB) and builds a separate SQLite file in `<HA configuration>/.storage/` per region. A temporary download and database need additional space for each import. A failed import keeps the previous completed catalogue for that selection. Adjacent countries can be selected together for cross-border trips. Scheduled refreshes require Home Assistant to be running; stale catalogues also start updating after restart. Imports run one at a time. A dependency-free PBF reader works on HA installations where `osmium` cannot be installed; if `osmium` is already available, imports use its faster parser. Large countries can take substantially longer with the built-in reader. OCM continues to provide charging stations.

The POI panel shows downloaded bytes, the advertised total and a progress bar during transfer. If the server does not supply a total, the bar remains indeterminate. The following database import is shown separately without a percentage because its duration cannot be inferred from transferred bytes.

Spatial queries merge and deduplicate vehicle-near POIs and POIs in the visible map area across the selected countries. MapLibre clusters markers, while GPS follow uses the nearby results for its 1–3 destinations. Set a map result ceiling of 500–10,000 (3,000 on first enabling the catalogue). This limits each request, not the number stored in the regional databases. Zoom or filter in very dense areas to see other places. Ways use their approximate coordinate center; POIs mapped only as OSM multipolygon relations are not included. Deselect all countries for the old general-POI live search (up to 200 km).

The catalogue is a periodic location snapshot, not a source of live opening hours or charger availability. OSM data © OpenStreetMap contributors, distributed via Geofabrik under the ODbL.

## Persistent data

DriveLoom stores its own persistent data in `<HA configuration>/.storage/driveloom.db`:

- GPS fixes, tracking settings and phone GPS source configuration;
- trip identities, merged trips, folders and assignments;
- vehicle consumption counters, daily history, source sensor observations and trip analytics counter samples;
- global date selections, route templates, destinations, POI templates, map preferences and server-side charging-station caches.

The optional POI catalogues are stored separately in `.storage/driveloom-pois-<region hash>.db` so each completed replacement can be activated atomically. An existing v0.1.9 `driveloom-pois.db` catalogue is migrated automatically when possible.

The daily consumption history remains a **daily_history table** rather than a separate ledger file. Map preferences are stored per Home Assistant user. Browser map tiles remain a disposable local cache; fullscreen state is temporary. The large charging-register CSV is downloaded to a temporary file and removed after parsing.

Home Assistant itself still owns the integration's configuration entries and credentials, the entity and device registries, dashboards, and any HA Recorder history. Those are outside this integration's database. Existing manual Recorder import for historical GPS points remains available; the new trip-consumption and SoC-repair queries use DriveLoom's own samples from installation onward. No import from Cardata Analytics and no backup/restore feature are included in this version.

Do not copy the live SQLite file while Home Assistant is writing to it: SQLite WAL files may hold uncheckpointed changes. A dedicated export/restore feature is outside this release.


## License

See [LICENSE](LICENSE).
