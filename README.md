# I-25 / Santa Fe Dr volume balance and corridor map

Two standalone pages. They link to each other through the buttons in their headers.

## Files

| File | What it is |
|---|---|
| `volume_balance.html` | The balancing tool that replaces `AK_Volume Balance.xlsx`. Double-click to open in Edge or Chrome. No server, no internet. |
| `network.json` | Its data: network drawing, scenarios, counts, locks, movements, imported StreetLight bins. |
| `corridor_map.html` | Map of the corridor: INRIX segments coloured by time of day, StreetLight intersections with movements, Replica trip origins and destinations by census tract. Needs internet for the basemap tiles and the MapLibre library only. |
| `map_data.json` | The map's data, also embedded in the page. |
| `tools/build_network.py` | One-time converter that produced `network.json` from the spreadsheet logic and the StreetLight CSV, and embeds a copy into the HTML. Re-run only to regenerate from scratch. |
| `tools/build_map.py` | Rebuilds `map_data.json` and re-embeds it. Re-run when the INRIX, StreetLight or Replica exports change (for example the full-year INRIX pull). Census tract centroids are cached in `tools/cache/`. |

## Corridor map

* **Slider** picks the 5-minute bin. INRIX segments recolour; the StreetLight panel follows the matching 15-minute bin. Play animates the day.
* **INRIX**: click a segment for its 24-hour speed profile, reference and historical speeds, and period averages. The current export is one averaged day; the profile bands return when the full-year export is rebuilt.
* **StreetLight**: click an intersection for the 12 movements at the slider bin and for the hour starting there, for the chosen day type.
* **Replica**: circles at tract centroids sized by trips starting (blue) or ending (orange) there. Filter by mode or purpose. "Replica summary" gives mode, purpose, county, duration, distance and start-time distributions for all trips in the export.

## Volume balance: new network from scratch

**New** clears the drawing and starts an empty network (optionally keeping the imported StreetLight sources so new intersection boxes can bind to them). Place nodes with the + tools, Connect them, type counts in the link panel, then **Save as…**.

## Daily workflow

1. Open `volume_balance.html`. It shows the embedded copy of the network.
2. Click **Open JSON…** and pick `network.json` once. From then on **Save** (or Ctrl+S) writes straight back to that file; next time, **Reconnect file** reopens it with one click.
3. Edit: click any link or intersection box, change values in the side panel, drag nodes to tidy the drawing. Unsaved work is also kept as a draft in the browser.

## How values are decided

Each link shows one balanced volume. Priority:

1. **Locked** – you typed it (black border, 🔒).
2. **Count** – the link's primary observed count, grown to the base year (Settings).
3. **Movements** – approach or departure sum from an adjacent intersection box.
4. **Balance** – solved by conservation of flow at junctions (dashed border, italic).

Chips under a value compare it with every other piece of evidence. Junctions that cannot balance show a red Δ. The side panel lists all issues; click one to jump to it.

Intersection boxes are bound to a StreetLight source; the scenario's day type and hour drive them (Settings), and any movement you type becomes an orange override.

## Extending the network

* **+ Junction / + Terminal / + Intersection** then click the canvas.
* **Connect**: click the upstream node, then the downstream node. For an intersection you pick the leg.
* **Import StreetLight CSV…**: drop any `*_tmc_full_table.csv`; it becomes a source you can bind boxes to.
* **Scenarios…**: duplicate the baseline for AM, future year, or alternatives. All scenarios share the drawing.
* **Export…**: links CSV, movements CSV, SVG or PNG of the diagram.

## Drawing tips (volume balance)

* **Connecting**: in Connect mode click a port on an intersection box (triangle pointing in = IN port, where a link ends; pointing out = OUT port, where a link starts) or a junction / terminal, then the other end. The direction follows the ports, so the click order does not matter and no leg question is asked. Free ports light up blue while connecting. Clicking a box body instead of a port still asks for the leg.
* **Opposite direction**: Shift+click the second end while connecting, tick "Also create the opposite direction" when a leg choice is asked, or press "Create opposite direction" in a link's panel. The reverse link takes the matching out/in ports on intersection legs. Every link gets its own attach point on a junction or terminal edge, in the direction it comes from; links from nearly the same direction are spread side by side (in-links on one side, out-links on the other), so paired streets run parallel and arrows never pile up on one point.
* **Placing several nodes**: + Junction, + Terminal and + Intersection stay active; click the canvas for each one and press Esc to return to Select.
* **Typing movements**: every movement inside an intersection box is a small entry box. Click it and type (Enter saves, Tab saves and moves to the next box, Esc cancels), or use the grid in the box's panel. On a StreetLight-bound box the typed value becomes an orange override; ↺ in the panel restores the source value. Observed counts (TCDS etc.) belong to links: click a link and use "+ add count".
* **Extra movements**: in an intersection panel, "+ add movement" offers U-turns and second turn lanes for every approach, or a custom entry-leg → exit-leg movement. They are typed values, counted in the approach and departure sums so the balance sees them, and kept per scenario like other movements. In the box they sit in driver order next to the standard movement they belong to: U-turn at the driver's far left, a second left after the left, a second right after the right. The box grows to fit.
* **Directional junctions**: a junction that is just a two-way street passing through (exactly two opposite-direction pairs) balances each direction on its own, so an eastbound mismatch never shows on the westbound links. The junction panel shows the sums per direction and lets you force either behaviour.
* **Leg ports**: each intersection box shows an in and an out port on every leg (filled = approach link attached, hollow = departure link attached, dashed = free). Hover a port for its name. Links of an opposite-direction pair are drawn side by side with their labels on opposite sides.

## Future steps

1. **INRIX full year**: rebuild `map_data.json` with the full-year export so the segment panel shows percentile bands and day-type profiles like the earlier INRIX map.

## Notes carried over from the spreadsheet

* `SB 6th–Alameda` is locked at 8055 against the 2020 count of 8495, as typed in the sheet.
* The sheet date 2027-11-02 at the I-25 SB count south of the Santa Fe ramps is treated as 2017-11-02.
* StreetLight "Santa Fe SB" reports SBL 1125 and SBT 1125 for the same continuing roadway; the box combines them as SBT 2250 (the sheet's 2647 through plus 397 right double-counted the right turns).
* Boxes use StreetLight "All Days" like the sheet. Switch the scenario day type to "Weekday (Tu-Th)" in Settings if the design hour should exclude weekends.
