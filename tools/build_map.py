"""Build the data for corridor_map.html from INRIX, StreetLight and Replica exports.

    python tools/build_map.py        # writes map_data.json and embeds it into corridor_map.html

Inputs (all in the project folder):
  TMC_Identification.csv, Santa-Fe-Model---I25---Travel-Times---5-minutes.csv   (INRIX)
  Streetlight TMC .../Shapefile/*.zip + network.json sources                     (StreetLight)
  replica-*/*.csv                                                                (Replica trips)
  Census 2020 gazetteer (tracts, counties) downloaded once into tools/cache/
"""
import csv, io, json, re, urllib.request, zipfile
from collections import Counter, defaultdict
from pathlib import Path

import shapefile  # pyshp

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "tools" / "cache"; CACHE.mkdir(exist_ok=True)
PAGE = ROOT / "corridor_map.html"
OUT = ROOT / "map_data.json"
MOV = ['NBL', 'NBT', 'NBR', 'SBL', 'SBT', 'SBR', 'EBL', 'EBT', 'EBR', 'WBL', 'WBT', 'WBR']


def read_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ road geometry via OSRM
import math, time

OSRM = "https://router.project-osrm.org/route/v1/driving/"
OSRM_CACHE = CACHE / "osrm"; OSRM_CACHE.mkdir(exist_ok=True)


def bearing(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[1], a[0], b[1], b[0]])
    x = math.sin(lo2 - lo1) * math.cos(la2); y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def haversine_mi(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[1], a[0], b[1], b[0]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def route_geometry(tmc, a, b, miles):
    """Road-following coordinates for a TMC from start a to end b (lon, lat). Tries a few
    snapping settings on the public OSRM server, keeps the candidate whose length is closest
    to the INRIX length, falls back to a straight line. Results are cached per TMC."""
    cp = OSRM_CACHE / f"{tmc}.json"
    if cp.exists():
        cands = json.loads(cp.read_text(encoding="utf-8"))
    else:
        br = round(bearing(a, b)); cands = []
        for rad, tol in ((25, 30), (50, 45), (100, 60), (50, None)):
            q = f"{a[0]},{a[1]};{b[0]},{b[1]}?overview=full&geometries=geojson&radiuses={rad};{rad}"
            if tol: q += f"&bearings={br},{tol};{br},{tol}"
            try:
                d = json.load(urllib.request.urlopen(OSRM + q, timeout=30))
                if d.get("routes"): cands.append({"rad": rad, "tol": tol, "mi": d["routes"][0]["distance"] / 1609.34, "coords": d["routes"][0]["geometry"]["coordinates"]})
            except Exception as e:
                cands.append({"rad": rad, "tol": tol, "err": str(e)[:80]})
            time.sleep(0.25)
        cp.write_text(json.dumps(cands), encoding="utf-8")
    straight = haversine_mi(a, b)
    target = miles if miles else max(straight, 0.01)

    def pick(cs):
        best = None
        for c in cs:
            if "coords" not in c or len(c["coords"]) < 2: continue
            ratio = c["mi"] / target
            if 0.6 <= ratio <= 1.6 and (best is None or abs(ratio - 1) < abs(best[0] - 1)): best = (ratio, c)
        return best

    best = pick(cands)
    if not best:
        # Second stage for ramps: ask OSRM for the nearest road candidates at each end and route
        # between candidate pairs; the ramp is the pair whose route length matches the TMC length.
        pp = OSRM_CACHE / f"{tmc}_pairs.json"
        if pp.exists():
            pairs = json.loads(pp.read_text(encoding="utf-8"))
        else:
            pairs = []
            try:
                near = lambda p: [w["location"] for w in json.load(urllib.request.urlopen(f"https://router.project-osrm.org/nearest/v1/driving/{p[0]},{p[1]}?number=6", timeout=30))["waypoints"] if w["distance"] <= 35]
                A, B = near(a), near(b); time.sleep(0.25)
                seen = set()
                for pa in A:
                    for pb in B:
                        key = (round(pa[0], 5), round(pa[1], 5), round(pb[0], 5), round(pb[1], 5))
                        if key in seen: continue
                        seen.add(key)
                        q = f"{pa[0]},{pa[1]};{pb[0]},{pb[1]}?overview=full&geometries=geojson&radiuses=8;8"
                        try:
                            d = json.load(urllib.request.urlopen(OSRM + q, timeout=30))
                            if d.get("routes"): pairs.append({"mi": d["routes"][0]["distance"] / 1609.34, "coords": d["routes"][0]["geometry"]["coordinates"]})
                        except Exception as e:
                            pairs.append({"err": str(e)[:80]})
                        time.sleep(0.2)
                        if pick(pairs): break
                    if pick(pairs): break
            except Exception as e:
                pairs.append({"err": str(e)[:80]})
            pp.write_text(json.dumps(pairs), encoding="utf-8")
        best = pick(pairs)
    if best:
        return [[round(x, 6), round(y, 6)] for x, y in best[1]["coords"]], False, round(best[1]["mi"], 3)
    return [[round(a[0], 6), round(a[1], 6)], [round(b[0], 6), round(b[1], 6)]], True, round(straight, 3)


# ------------------------------------------------------------------ INRIX
def build_inrix():
    ident = {r["tmc"]: r for r in read_csv(ROOT / "TMC_Identification.csv")}
    tt_rows = read_csv(next(ROOT.glob("*Travel-Times*.csv")))
    prof = defaultdict(lambda: {"spd": [None] * 288, "tt": [None] * 288, "ref": None, "hist": [None] * 288, "conf": [None] * 288})
    dates = set()
    for r in tt_rows:
        ts = r["measurement_tstamp"]; dates.add(ts[:10])
        h, m = int(ts[11:13]), int(ts[14:16]); i = h * 12 + m // 5
        p = prof[r["tmc_code"]]
        p["spd"][i] = float(r["speed"]) if r["speed"] else None
        p["tt"][i] = float(r["travel_time_minutes"]) if r["travel_time_minutes"] else None
        p["hist"][i] = float(r["historical_average_speed"]) if r["historical_average_speed"] else None
        p["conf"][i] = float(r["confidence_score"]) if r["confidence_score"] else None
        if r["reference_speed"]: p["ref"] = float(r["reference_speed"])
    feats = []
    for tmc, p in prof.items():
        d = ident.get(tmc)
        if not d: continue
        road = d["road"] or d["direction"]; direction = d["direction"] if d["road"] else ""
        a = (float(d["start_longitude"]), float(d["start_latitude"])); b = (float(d["end_longitude"]), float(d["end_latitude"]))
        coords, straight, routed_mi = route_geometry(tmc, a, b, float(d["miles"] or 0))
        feats.append({"type": "Feature", "id": tmc, "geometry": {"type": "LineString", "coordinates": coords},
                      "properties": {"tmc": tmc, "road": road, "direction": direction, "at": d["intersection"], "miles": round(float(d["miles"]), 3), "ref": p["ref"], "straight": straight, "routedMi": routed_mi,
                                     "spd": [round(x, 1) if x is not None else None for x in p["spd"]], "tt": [round(x, 2) if x is not None else None for x in p["tt"]],
                                     "hist": [round(x, 1) if x is not None else None for x in p["hist"]], "conf": p["conf"]}})
    note = f"INRIX 5-minute profile, {', '.join(sorted(dates))} (averaged export; full-year pull pending)"
    return {"type": "FeatureCollection", "features": feats}, note


# ------------------------------------------------------------------ StreetLight
def build_stl():
    net = json.loads((ROOT / "network.json").read_text(encoding="utf-8"))
    src = net["sources"]["stl_2098249"]
    zpath = next((ROOT / "Streetlight TMC 2098249_S_Platter_River_Dr" / "Shapefile").glob("*.zip"))
    z = zipfile.ZipFile(zpath); names = {Path(n).suffix: n for n in z.namelist()}
    r = shapefile.Reader(shp=io.BytesIO(z.read(names[".shp"])), dbf=io.BytesIO(z.read(names[".dbf"])), shx=io.BytesIO(z.read(names[".shx"])))
    gates = defaultdict(list)
    for sr in r.iterShapeRecords():
        pts = sr.shape.points
        if not pts: continue
        rec = sr.record.as_dict()
        mid = [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
        gates[rec["int_name"]].append({"role": rec["gate_role"], "road": rec["gate_road"], "dir": rec["gate_direc"], "line": [[round(p[0], 6), round(p[1], 6)] for p in pts], "mid": [round(mid[0], 6), round(mid[1], 6)]})
    feats = []
    for name, gs in gates.items():
        cx = sum(g["mid"][0] for g in gs) / len(gs); cy = sum(g["mid"][1] for g in gs) / len(gs)
        feats.append({"type": "Feature", "id": name, "geometry": {"type": "Point", "coordinates": [round(cx, 6), round(cy, 6)]},
                      "properties": {"name": name, "gates": gs, "hasData": name in src["data"]}})
    return {"points": {"type": "FeatureCollection", "features": feats}, "source": {"name": src["name"], "period": src["period"], "data": src["data"]}}


# ------------------------------------------------------------------ Replica
def gazetteer(name):
    p = CACHE / name.replace(".zip", ".txt")
    if not p.exists():
        data = urllib.request.urlopen("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/" + name, timeout=120).read()
        z = zipfile.ZipFile(io.BytesIO(data)); txt = z.read(z.namelist()[0]).decode("latin-1"); p.write_text(txt, encoding="utf-8")
    rows = [l.rstrip().split("\t") for l in p.read_text(encoding="utf-8").splitlines()]
    hdr = [h.strip() for h in rows[0]]
    return [dict(zip(hdr, [c.strip() for c in r])) for r in rows[1:]]


def build_replica():
    f = next(ROOT.glob("replica-*/*.csv"))
    rows = read_csv(f)
    readme = next(ROOT.glob("replica-*/README.txt")).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Time Period:\s*(.+)", readme); period = m.group(1).strip() if m else ""
    m = re.search(r"\{Time:\s*([^}]+)\}", readme); window = m.group(1).strip() if m else ""
    counties = {(c["USPS"], c["NAME"]): c["GEOID"] for c in gazetteer("2020_Gaz_counties_national.zip")}
    tracts = {t["GEOID"]: (float(t["INTPTLONG"]), float(t["INTPTLAT"])) for t in gazetteer("2020_Gaz_tracts_national.zip")}

    def geoid(s):  # "55.51 (Arapahoe, CO)" -> 08005005551
        m = re.match(r"\s*([\d.]+)\s*\((.+?),\s*(\w\w)\)", s or "")
        if not m: return None
        code, cty, st = m.groups(); whole, _, frac = code.partition(".")
        fips = counties.get((st, cty + " County")) or counties.get((st, cty)) or next((v for (s2, n), v in counties.items() if s2 == st and n.startswith(cty)), None)
        if not fips: return None
        return fips + f"{int(whole):04d}{(frac + '00')[:2]}"

    modes = sorted({r["primary_mode"] for r in rows}); purposes = sorted({r["trip_purpose"] for r in rows})
    mi = {m: i for i, m in enumerate(modes)}; pi = {p: i for i, p in enumerate(purposes)}
    T = {}
    def tract(g, name):
        if g not in T: T[g] = {"g": g, "name": name, "o": 0, "d": 0, "om": [0] * len(modes), "dm": [0] * len(modes), "op": [0] * len(purposes), "dp": [0] * len(purposes)}
        return T[g]
    summ = {"n": len(rows), "mode": Counter(), "purpose": Counter(), "vehicle": Counter(), "ocounty": Counter(), "dcounty": Counter(), "dur": Counter(), "dist": Counter(), "start": Counter(), "unmatched": 0}
    for r in rows:
        og, dg = geoid(r["origin_trct_2020"]), geoid(r["destination_trct_2020"])
        summ["mode"][r["primary_mode"]] += 1; summ["purpose"][r["trip_purpose"]] += 1; summ["vehicle"][r["vehicle_type"] or "n/a"] += 1
        summ["ocounty"][r["origin_cty_2020"]] += 1; summ["dcounty"][r["destination_cty_2020"]] += 1
        try: summ["dur"][min(120, int(float(r["trip_duration_minutes"]) // 5 * 5))] += 1
        except: pass
        try: summ["dist"][min(60, int(float(r["trip_distance_miles"]) // 2 * 2))] += 1
        except: pass
        summ["start"][r["trip_start_time"][:5][:4] + "0"] += 1
        for g, name, key, km, kp in ((og, r["origin_trct_2020"], "o", "om", "op"), (dg, r["destination_trct_2020"], "d", "dm", "dp")):
            if g and g in tracts:
                t = tract(g, name); t[key] += 1; t[km][mi[r["primary_mode"]]] += 1; t[kp][pi[r["trip_purpose"]]] += 1
            else: summ["unmatched"] += 1
    tl = [[t["g"], t["name"], round(tracts[t["g"]][0], 5), round(tracts[t["g"]][1], 5), t["o"], t["d"], t["om"], t["dm"], t["op"], t["dp"]] for t in T.values()]
    for k in ("mode", "purpose", "vehicle", "ocounty", "dcounty"): summ[k] = sorted(summ[k].items(), key=lambda x: -x[1])
    for k in ("dur", "dist"): summ[k] = sorted(summ[k].items())
    summ["start"] = sorted(summ["start"].items())
    return {"period": period, "window": window, "file": f.name, "modes": modes, "purposes": purposes, "tracts": tl, "summary": summ}


def embed(data):
    html = PAGE.read_text(encoding="utf-8")
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    new = re.sub(r'(<script id="map-data" type="application/json">).*?(</script>)', lambda m: m.group(1) + blob + m.group(2), html, count=1, flags=re.S)
    PAGE.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    inrix, inote = build_inrix()
    stl = build_stl()
    rep = build_replica()
    data = {"meta": {"built": "2026-11-02", "center": [-104.995, 39.705], "zoom": 13.2, "inrixNote": inote},
            "inrix": inrix, "stl": stl, "replica": rep}
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    embed(data)
    ns = sum(1 for f in inrix["features"] if f["properties"]["straight"])
    print(f"INRIX {len(inrix['features'])} segments ({ns} straight fallbacks: {', '.join(f['id'] for f in inrix['features'] if f['properties']['straight'])}) · StreetLight {len(stl['points']['features'])} intersections · Replica {len(rep['tracts'])} tracts, {rep['summary']['unmatched']} unmatched ends · {OUT.stat().st_size // 1024} KB")
