# DriveLoom

DriveLoom is an independent Home Assistant integration for vehicle analytics, GPS tracks, trips and map views. DriveLoom starts with an empty database and can run beside Cardata Analytics. It does **not** read or migrate data from Cardata Analytics.

## Installation

Copy `custom_components/driveloom` to the matching folder below your Home Assistant configuration directory, restart Home Assistant and add **DriveLoom** through **Settings → Devices & services → Add integration**. Configure each vehicle with its source entities. Home Assistant 2026.1.0 or newer is required. This repository also includes `hacs.json` for HACS custom-repository installation.

The integration registers its dashboard card as a Lovelace resource automatically when Lovelace uses storage mode. Add `custom:driveloom-card` for the analytics overview or `custom:driveloom-map-card` for the map. In YAML resource mode, replace the old resource with `/driveloom/driveloom-card-0.1.4.js?v=0.1.4` as a JavaScript module.

On the map, GPS toggles live follow independently of OSM, OSM+, Topo, Satellite and 3D. Choose a style or zoom while following; a deliberate drag or another fit/track action exits live follow. With successive reliable position fixes, the map turns to keep the direction of travel at the top. The live camera uses the vehicle's current position, including a configured phone source; historical track markers do not control the camera.

With POIs selected, live follow can show up to three nearest loaded, filtered POIs ahead of the vehicle and their straight-line distances in larger mobile-friendly rows. If fewer match, fewer rows are shown. The POI panel has a switch for these suggestions. Multiple selected charging networks (such as IONITY, EnBW and Tesla) are treated as alternatives. Tap any destination, then confirm its Google Maps navigation link. The straight-line distance does not represent the road route, and live suggestions require a recent reliable movement heading. To try the same selection and confirmation UI while parked, tap **Test POI suggestion** in the POI panel. The two-minute preview uses the three nearest loaded POIs around the vehicle without a direction filter and is explicitly labeled as a preview.

## Persistent data

DriveLoom stores its own persistent data in `<HA configuration>/.storage/driveloom.db`:

- GPS fixes, tracking settings and phone GPS source configuration;
- trip identities, merged trips, folders and assignments;
- vehicle consumption counters, daily history, source sensor observations and trip analytics counter samples;
- global date selections, route templates, destinations, POI templates, map preferences and server-side charging-station caches.

The daily consumption history remains a **daily_history table** rather than a separate ledger file. Map preferences are stored per Home Assistant user. Browser map tiles remain a disposable local cache; fullscreen state is temporary. The large charging-register CSV is downloaded to a temporary file and removed after parsing.

Home Assistant itself still owns the integration's configuration entries and credentials, the entity and device registries, dashboards, and any HA Recorder history. Those are outside this integration's database. Existing manual Recorder import for historical GPS points remains available; the new trip-consumption and SoC-repair queries use DriveLoom's own samples from installation onward. No import from Cardata Analytics and no backup/restore feature are included in this version.

Do not copy the live SQLite file while Home Assistant is writing to it: SQLite WAL files may hold uncheckpointed changes. A dedicated export/restore feature is outside this release.


## License

See [LICENSE](LICENSE).
