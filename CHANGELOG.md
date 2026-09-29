# Changelog

## 0.1.2 — Live GPS follow camera

- Keep GPS follow active across OSM, OSM+, Topo, Satellite and 3D, with the chosen zoom preserved and the active style shown alongside GPS.
- Recenter after phone GPS status updates (checked every five seconds during live follow) and style changes; keep the existing MapLibre map instance while the vehicle moves.
- Rotate the live map toward the direction of successive plausible fixes, retaining the last reliable heading through jitter, stops and gaps.
- Allow the GPS button to turn follow off; intentional panning and historical track actions still release the live camera.
- Bundle both Lovelace cards under the versioned `driveloom-card-0.1.2.js` resource.

## 0.1.1 — Entity name translations

- Show each sensor's translated function beside its vehicle name instead of repeating only the vehicle name.
- Apply the same correction to the global date and select controls.
- Keep unique IDs and existing entity IDs unchanged.

## 0.1.0 — Initial DriveLoom package

- Independent Home Assistant integration and Lovelace cards based on the tested Cardata Analytics 0.1.75 behavior.
- All DriveLoom-owned persistent vehicle, GPS, trip, route, template and map-preference data use one SQLite database.
- Daily consumption history and newly observed source and calculated counter samples are stored in database tables.
- Trip analytics and SoC repairs use DriveLoom samples; historical data from Cardata Analytics is not imported.
- No database backup or restore function in this release.
