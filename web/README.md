# Offline reviewer interface

The renderer in `src/crw/render.py` embeds a completed demo report into one standalone HTML file. There are no external fonts, CDNs, image files, network fetches, telemetry or AI-service dependencies. The source template lives inside the Python package so a built wheel can generate the same interface without depending on the checkout layout.

Generate the reviewer file with:

```bash
crw demo --customers 1000 --transactions 80 --research --out runs/demo
```

Open `runs/demo/workbench.html` directly in a browser or through a loopback file server. This interface contains the full run summary and a deterministic selection of customer examples spread across the score range. It labels that selection explicitly and does not claim to browse every generated customer. The full exported assessments remain available in the run directory.

## Design and interaction

The interface uses a navy work area, slate evidence panels, muted teal for known evidence, amber for review context, and visible textual status labels. Color never carries a status alone. A system sans-serif stack avoids network font loading. The layout gives customer evidence and dense review tables priority over decorative KPI tiles.

Eight keyboard-accessible views separate portfolio context, customer explanation, executable scenarios, compound review hypotheses, feature definitions, synthetic research, sensitivity and adoption evidence. Arrow keys, Home and End navigate the tab set. Search and filters use labeled controls. Tables retain accessible headers; calibration plots include textual descriptions and their underlying data table. The layout supports narrow screens and printing the currently selected view.

The illustrative band controls recompute only the classification implied by stored bounds under new band minima. They retain mandatory missing-evidence and history-completeness gates, reevaluate whether uncertainty crosses a revised boundary, and never alter the underlying index, stored assessment or trained model. Their JavaScript helpers have focused cross-boundary tests.

## Evidence and safety

JSON is embedded in a non-executing `application/json` element. Script-terminating characters and Unicode line separators are escaped at serialization, and dynamic strings are HTML-escaped when inserted into the interface. A local export button downloads the already embedded report; it sends nothing to a remote service.

This is an offline research viewer, not an access-controlled multi-user product. Do not place non-public institutional data into this public reference workflow. An institution's approved implementation needs its own deployment, security, validation and operating controls.
