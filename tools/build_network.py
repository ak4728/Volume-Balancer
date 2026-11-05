"""Build network.json for volume_balance.html from the spreadsheet logic and the
StreetLight TMC export, then embed it into the page.

    python tools/build_network.py            # writes network.json, embeds into volume_balance.html

Nodes/links below reproduce AK_Volume Balance.xlsx (sheet "Baseline (5PM)") as a graph:
I-25 SB/NB mainline with ramps, the Kalamath / Santa Fe pair north of the interchange and
the Santa Fe arterial south of it with StreetLight intersection boxes.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STL_CSV = ROOT / "Streetlight TMC 2098249_S_Platter_River_Dr" / "2098249_S_Platter_River_Dr_tmc_full_table.csv"
OUT_JSON = ROOT / "network.json"
PAGE = ROOT / "volume_balance.html"
MOV = ['NBL', 'NBT', 'NBR', 'SBL', 'SBT', 'SBR', 'EBL', 'EBT', 'EBR', 'WBL', 'WBT', 'WBR']

NODES, LINKS, SC_LINKS, SC_TMC = [], [], {}, {}


def N(id, type, label, x, y):
    NODES.append({"id": id, "type": type, "label": label, "x": x, "y": y})


def L(id, frm, to, cls, label=None, obs=None, mode=None, balanced=None, fromLeg=None, toLeg=None, labelT=None, note=None, labelDx=None, labelDy=None, chipsUp=False):
    d = {"id": id, "from": frm, "to": to, "cls": cls}
    if label: d["label"] = label
    if fromLeg: d["fromLeg"] = fromLeg
    if toLeg: d["toLeg"] = toLeg
    if labelT is not None: d["labelT"] = labelT
    if labelDx: d["labelDx"] = labelDx
    if labelDy: d["labelDy"] = labelDy
    if chipsUp: d["chipsUp"] = True
    LINKS.append(d)
    s = {}
    if obs: s["observed"] = [{"source": o[0], "date": o[1], "value": o[2]} for o in obs]
    if mode: s["mode"] = mode
    if balanced is not None: s["balanced"] = balanced
    if note: s["note"] = note
    if s: SC_LINKS[id] = s


def TMC(id, label, x, y, intersection=None, overrides=None, note=None):
    N(id, "tmc", label, x, y)
    t = {}
    if intersection: t["source"] = {"id": "stl_2098249", "intersection": intersection}
    if overrides: t["overrides"] = {k: True for k in overrides}; t["movements"] = dict(overrides)
    if note: t["note"] = note
    SC_TMC[id] = t


T = "TCDS"
# ------------------------------------------------------------------ I-25 SB (top = north)
SB, NB = 700, 860
N("sb_n", "terminal", "I-25 SB from north", SB, 20)
N("sb_8th_off", "junction", "", SB, 150); N("sb_8th_on", "junction", "", SB, 210)
N("sb_6th_off", "junction", "", SB, 340); N("sb_6th_on", "junction", "", SB, 440)
N("sb_alameda_off", "junction", "", SB, 580)
N("sb_sf_off", "junction", "", SB, 700); N("sb_sf_on", "junction", "", SB, 790)
N("sb_bwy_off", "junction", "", SB, 930); N("sb_frontage_off", "junction", "", SB, 990); N("sb_frontage_on", "junction", "", SB, 1050)
N("sb_s", "terminal", "I-25 SB to south", SB, 1180)
N("t_sb_8th_off", "terminal", "8th Ave off", 520, 150); N("t_sb_8th_on", "terminal", "8th Ave on", 520, 210)
N("sb_6th_off_split", "junction", "", 560, 340); N("t_sb_6th_off_wb", "terminal", "to 6th Ave WB", 420, 310); N("t_sb_6th_off_eb", "terminal", "to 6th Ave EB", 420, 370)
N("sb_6th_on_merge", "junction", "", 560, 440); N("t_sb_6th_on_wb", "terminal", "from 6th Ave WB", 420, 410); N("t_sb_6th_on_eb", "terminal", "from 6th Ave EB", 420, 470)
N("t_sb_alameda_off", "terminal", "Alameda off", 520, 580)
N("t_sb_bwy_off", "terminal", "S Broadway off", 520, 930); N("t_sb_frontage_off", "terminal", "Frontage off", 520, 990); N("t_sb_frontage_on", "terminal", "Frontage on", 520, 1050)

L("i25sb_n_8th", "sb_n", "sb_8th_off", "interstate", "SB north of 8th")
L("ramp_sb_8th_off", "sb_8th_off", "t_sb_8th_off", "ramp", obs=[(T, None, 457)])
L("i25sb_8th_mid", "sb_8th_off", "sb_8th_on", "interstate")
L("ramp_sb_8th_on", "t_sb_8th_on", "sb_8th_on", "ramp", obs=[(T, None, 369)])
L("i25sb_8th_6th", "sb_8th_on", "sb_6th_off", "interstate", "SB 8th–6th")
L("ramp_sb_6th_off", "sb_6th_off", "sb_6th_off_split", "ramp", "6th Ave off")
L("ramp_sb_6th_off_wb", "sb_6th_off_split", "t_sb_6th_off_wb", "ramp", obs=[(T, "2020-09-30", 1969)])
L("ramp_sb_6th_off_eb", "sb_6th_off_split", "t_sb_6th_off_eb", "ramp", obs=[(T, "2020-08-04", 289)])
L("i25sb_6th_mid", "sb_6th_off", "sb_6th_on", "interstate")
L("ramp_sb_6th_on", "sb_6th_on_merge", "sb_6th_on", "ramp", "6th Ave on")
L("ramp_sb_6th_on_wb", "t_sb_6th_on_wb", "sb_6th_on_merge", "ramp", obs=[(T, "2020-07-14", 293)])
L("ramp_sb_6th_on_eb", "t_sb_6th_on_eb", "sb_6th_on_merge", "ramp", obs=[(T, "2020-07-14", 2274)])
L("i25sb_6th_alameda", "sb_6th_on", "sb_alameda_off", "interstate", "SB 6th–Alameda", obs=[(T, "2020-08-04", 8495)], mode="lock", balanced=8055,
  note="Spreadsheet AV30: typed 8055 against the 2020 count of 8495 (-5.2%).")
L("ramp_sb_alameda_off", "sb_alameda_off", "t_sb_alameda_off", "ramp", obs=[(T, "2017-04-25", 678)])
L("i25sb_alameda_sf", "sb_alameda_off", "sb_sf_off", "interstate", "SB Alameda–Santa Fe")
L("ramp_sb_sf_off", "sb_sf_off", "sfsb_merge", "ramp", "Exit to Santa Fe SB", obs=[(T, "2017-11-02", 2551)], labelT=0.15)
L("i25sb_sf_mid", "sb_sf_off", "sb_sf_on", "interstate")
L("ramp_sb_sf_on", "kal_diverge", "sb_sf_on", "ramp", "Kalamath on-ramp", obs=[(T, "2017-11-02", 511)], labelT=0.6)
L("i25sb_sf_bwy", "sb_sf_on", "sb_bwy_off", "interstate", "SB Santa Fe–Broadway", obs=[(T, "2017-11-02", 5588)],
  note="Spreadsheet AR60 shows 2027-11-02; assumed 2017-11-02 like the other interchange counts.")
L("ramp_sb_bwy_off", "sb_bwy_off", "t_sb_bwy_off", "ramp", obs=[(T, "2020-07-16", 323)])
L("i25sb_bwy_mid", "sb_bwy_off", "sb_frontage_off", "interstate")
L("ramp_sb_frontage_off", "sb_frontage_off", "t_sb_frontage_off", "ramp", obs=[(T, "2022-10-11", 1343)])
L("i25sb_frontage_mid", "sb_frontage_off", "sb_frontage_on", "interstate")
L("ramp_sb_frontage_on", "t_sb_frontage_on", "sb_frontage_on", "ramp", obs=[(T, "2020-07-16", 1500)])
L("i25sb_arkansas", "sb_frontage_on", "sb_s", "interstate", "SB at Arkansas Ave", obs=[(T, "2010-10-19", 7164)], mode="derive",
  note="Spreadsheet derives this (AV74) and compares with the 2010 count.")

# ------------------------------------------------------------------ I-25 NB (bottom = south)
N("nb_n", "terminal", "I-25 NB to north", NB, 20)
N("nb_8th_on", "junction", "", NB, 150); N("nb_8th_off", "junction", "", NB, 250)
N("nb_6th_on", "junction", "", NB, 340); N("nb_6th_off", "junction", "", NB, 440)
N("nb_cedar_on", "junction", "", NB, 580)
N("nb_sf_on", "junction", "", NB, 700); N("nb_sf_off", "junction", "", NB, 790)
N("nb_ohio_on", "junction", "", NB, 930); N("nb_wash_on", "junction", "", NB, 990); N("nb_ohio_off", "junction", "", NB, 1050)
N("nb_s", "terminal", "I-25 NB from south", NB, 1180)
N("t_nb_8th_on", "terminal", "8th Ave on", 1040, 150); N("t_nb_8th_off", "terminal", "8th Ave off", 1040, 250)
N("nb_6th_on_merge", "junction", "", 1000, 340); N("t_nb_6th_on_wb", "terminal", "from 6th Ave WB", 1140, 310); N("t_nb_6th_on_eb", "terminal", "from 6th Ave EB", 1140, 370)
N("nb_6th_off_split", "junction", "", 1000, 440); N("t_nb_6th_off_wb", "terminal", "to 6th Ave WB", 1140, 410); N("t_nb_6th_off_eb", "terminal", "to 6th Ave EB", 1140, 470)
N("t_nb_cedar_on", "terminal", "Cedar on", 1040, 580)
N("t_nb_ohio_on", "terminal", "Ohio Ave on", 1040, 930); N("t_nb_wash_on", "terminal", "S Washington on", 1040, 990); N("t_nb_ohio_off", "terminal", "Ohio Ave off", 1040, 1050)

L("i25nb_arkansas", "nb_s", "nb_ohio_off", "interstate", "NB at Arkansas Ave", obs=[(T, "2010-10-19", 4119)])
L("ramp_nb_ohio_off", "nb_ohio_off", "t_nb_ohio_off", "ramp", obs=[(T, "2020-07-15", 1377)])
L("i25nb_ohio_wash", "nb_ohio_off", "nb_wash_on", "interstate")
L("ramp_nb_wash_on", "t_nb_wash_on", "nb_wash_on", "ramp", obs=[(T, "2020-07-15", 1377)])
L("i25nb_wash_ohio", "nb_wash_on", "nb_ohio_on", "interstate")
L("ramp_nb_ohio_on", "t_nb_ohio_on", "nb_ohio_on", "ramp", obs=[(T, "2020-09-15", 202)])
L("i25nb_ohio_sf", "nb_ohio_on", "nb_sf_off", "interstate", "NB Broadway–Santa Fe", obs=[(T, "2017-11-02", 5040)])
L("ramp_nb_sf_off", "nb_sf_off", "sfnb_merge", "ramp", "Exit to Santa Fe NB", obs=[(T, "2017-11-02", 1203)], labelT=0.35)
L("i25nb_sf_mid", "nb_sf_off", "nb_sf_on", "interstate")
L("ramp_nb_sf_on", "sfnb_diverge", "nb_sf_on", "ramp", "Santa Fe on-ramp", obs=[(T, "2017-11-02", 1150)], labelT=0.55)
L("i25nb_sf_cedar", "nb_sf_on", "nb_cedar_on", "interstate", "NB Santa Fe–Cedar")
L("ramp_nb_cedar_on", "t_nb_cedar_on", "nb_cedar_on", "ramp", obs=[(T, "2017-04-25", 334)])
L("i25nb_cedar_6th", "nb_cedar_on", "nb_6th_off", "interstate", "NB Alameda–6th", obs=[(T, "2020-08-04", 7135)])
L("ramp_nb_6th_off", "nb_6th_off", "nb_6th_off_split", "ramp", "6th Ave off")
L("ramp_nb_6th_off_wb", "nb_6th_off_split", "t_nb_6th_off_wb", "ramp", obs=[(T, "2020-07-14", 1164)])
L("ramp_nb_6th_off_eb", "nb_6th_off_split", "t_nb_6th_off_eb", "ramp", obs=[(T, "2020-07-14", 52)])
L("i25nb_6th_mid", "nb_6th_off", "nb_6th_on", "interstate")
L("ramp_nb_6th_on", "nb_6th_on_merge", "nb_6th_on", "ramp", "6th Ave on")
L("ramp_nb_6th_on_wb", "t_nb_6th_on_wb", "nb_6th_on_merge", "ramp", obs=[(T, "2020-08-04", 454)])
L("ramp_nb_6th_on_eb", "t_nb_6th_on_eb", "nb_6th_on_merge", "ramp", obs=[(T, "2020-07-14", 1569)])
L("i25nb_6th_8th", "nb_6th_on", "nb_8th_off", "interstate", "NB 6th–8th")
L("ramp_nb_8th_off", "nb_8th_off", "t_nb_8th_off", "ramp", obs=[(T, "2022-07-27", 155)])
L("i25nb_8th_mid", "nb_8th_off", "nb_8th_on", "interstate", "NB at 8th Ave", obs=[(T, "2022-08-31", 7018)])
L("ramp_nb_8th_on", "t_nb_8th_on", "nb_8th_on", "ramp", obs=[(T, "2021-11-04", 652)])
L("i25nb_8th_n", "nb_8th_on", "nb_n", "interstate", "NB north of 8th")

# ------------------------------------------------------------------ Kalamath / Santa Fe north of I-25
KX, FX = 1350, 1700
N("kal_n", "terminal", "S Kalamath St (SB) from Alameda", KX, 520)
N("kal_diverge", "junction", "", KX, 640)
N("sfsb_merge", "junction", "", KX, 790)
N("sfnb_n", "terminal", "S Santa Fe Dr (NB) to Alameda", FX, 520)
N("sfnb_merge", "junction", "", FX, 640)
N("sfnb_diverge", "junction", "", FX, 790)
L("kal_alameda_i25", "kal_n", "kal_diverge", "street", "Kalamath SB at Alameda", obs=[(T, "2020-10-20", 1132)], mode="derive",
  note="Spreadsheet BS46 derives this from the 2013 Santa Fe SB count and compares with the 2020 count.")
L("kal_mid", "kal_diverge", "sfsb_merge", "street", "Kalamath SB under I-25")
L("sfsb_i25_miss", "sfsb_merge", "tmc_miss_w", "street", "Santa Fe SB, I-25 to Mississippi", obs=[(T, "2013-04-23", 3236)], toLeg="N")
L("sfnb_miss_i25", "tmc_miss_e", "sfnb_diverge", "street", "Santa Fe NB, Mississippi to I-25", obs=[(T, "2013-04-23", 2471)], fromLeg="N")
L("sfnb_mid", "sfnb_diverge", "sfnb_merge", "street", "Santa Fe NB under I-25")
L("sfnb_i25_alameda", "sfnb_merge", "sfnb_n", "street", "Santa Fe NB at Alameda", obs=[(T, "2020-09-15", 2656)], mode="derive",
  note="Spreadsheet BZ46 derives this and compares with the 2020 count.")

# ------------------------------------------------------------------ Santa Fe arterial south of I-25
TMC("tmc_miss_w", "S Platte River Dr (SB) @ Mississippi", KX, 960, "Mississippi West")
TMC("tmc_miss_e", "Santa Fe Dr (NB) @ Mississippi", FX, 960, "Mississippi East")
N("t_miss_west", "terminal", "Mississippi Ave west", 1150, 960)
N("t_miss_east", "terminal", "Mississippi Ave east", 1900, 960)
L("miss_w_in", "t_miss_west", "tmc_miss_w", "street", "EB approach", toLeg="W", labelDy=18)
L("miss_w_out", "tmc_miss_w", "t_miss_west", "street", "WB departure", fromLeg="W", labelDy=-18)
L("miss_mid_eb", "tmc_miss_w", "tmc_miss_e", "street", "Mississippi EB mid-block", fromLeg="E", toLeg="W", labelDy=14)
L("miss_mid_wb", "tmc_miss_e", "tmc_miss_w", "street", "Mississippi WB mid-block", fromLeg="W", toLeg="E", labelDy=-26, chipsUp=True)
L("miss_e_in", "t_miss_east", "tmc_miss_e", "street", "WB approach", toLeg="E", labelDy=-18)
L("miss_e_out", "tmc_miss_e", "t_miss_east", "street", "EB departure", fromLeg="E", labelDy=18)

TMC("tmc_sfsb_split", "Santa Fe SB split (S Platte River Dr W)", KX, 1250, "Santa Fe SB", overrides={"SBT": 2250, "SBL": 0},
    note="StreetLight reports SBL 1125 and SBT 1125 for the same roadway continuing south (plus SBR 397). Combined as SBT 2250. The spreadsheet typed 2647 as through, which double-counted the 397 right turns in its approach total (3044).")
N("t_platte_w", "terminal", "S Platte River Dr W", 1150, 1250)
L("sfsb_miss_split", "tmc_miss_w", "tmc_sfsb_split", "street", "Santa Fe SB, Mississippi to split", fromLeg="S", toLeg="N")
L("sfsb_split_w", "tmc_sfsb_split", "t_platte_w", "street", "to S Platte River Dr W", fromLeg="W")

TMC("tmc_ariz_sb", "Santa Fe Dr (SB) @ Arizona", KX, 1540, "Intersection 05", note="StreetLight 'Intersection 05' = SB through just north of Arizona (no cross-street movements captured).")
TMC("tmc_ariz_nb", "Santa Fe Dr (NB) @ Arizona", FX, 1540, "Arizona")
N("t_ariz_nb_w", "terminal", "S Platte River Dr E", 1500, 1560)
N("t_ariz_nb_e", "terminal", "W Arizona Ave", 1900, 1540)
L("sfsb_split_ariz", "tmc_sfsb_split", "tmc_ariz_sb", "street", "Santa Fe SB, split to Arizona", fromLeg="S", toLeg="N")
L("ariz_nb_w_in", "t_ariz_nb_w", "tmc_ariz_nb", "street", toLeg="W", labelDy=18)
L("ariz_nb_w_out", "tmc_ariz_nb", "t_ariz_nb_w", "street", fromLeg="W", labelDy=-18)
L("ariz_nb_e_in", "t_ariz_nb_e", "tmc_ariz_nb", "street", toLeg="E", labelDy=-18)
L("ariz_nb_e_out", "tmc_ariz_nb", "t_ariz_nb_e", "street", fromLeg="E", labelDy=18)
L("sfnb_ariz_miss", "tmc_ariz_nb", "tmc_miss_e", "street", "Santa Fe NB, Arizona to Mississippi", fromLeg="N", toLeg="S")

TMC("tmc_lou_nb", "Santa Fe Dr (NB) @ Louisiana", FX, 1830, "Lousiana")
N("t_lou_e", "terminal", "W Louisiana Ave", 1900, 1830)
L("lou_e_in", "t_lou_e", "tmc_lou_nb", "street", toLeg="E", labelDy=-18)
L("lou_e_out", "tmc_lou_nb", "t_lou_e", "street", fromLeg="E", labelDy=18)
L("sfnb_lou_ariz", "tmc_lou_nb", "tmc_ariz_nb", "street", "Santa Fe NB, Louisiana to Arizona", fromLeg="N", toLeg="S")

TMC("tmc_florida", "Santa Fe Dr @ Florida", 1525, 2120, "Florida")
N("t_florida_w", "terminal", "W Florida Ave west", 1300, 2120)
N("t_florida_e", "terminal", "W Florida Ave east", 1750, 2120)
N("t_florida_s", "terminal", "Santa Fe Dr south of Florida", 1525, 2320)
L("sfsb_ariz_florida", "tmc_ariz_sb", "tmc_florida", "street", "Santa Fe SB, Arizona to Florida", fromLeg="S", toLeg="N")
L("sfnb_florida_lou", "tmc_florida", "tmc_lou_nb", "street", "Santa Fe NB, Florida to Louisiana", fromLeg="N", toLeg="S")
L("florida_s_in", "t_florida_s", "tmc_florida", "street", "NB from south", toLeg="S", labelDx=34)
L("florida_s_out", "tmc_florida", "t_florida_s", "street", "SB to south", fromLeg="S", labelDx=-34)
L("florida_w_in", "t_florida_w", "tmc_florida", "street", toLeg="W", labelDy=18)
L("florida_w_out", "tmc_florida", "t_florida_w", "street", fromLeg="W", labelDy=-18)
L("florida_e_in", "t_florida_e", "tmc_florida", "street", toLeg="E", labelDy=-18)
L("florida_e_out", "tmc_florida", "t_florida_e", "street", fromLeg="E", labelDy=18)


# ------------------------------------------------------------------ StreetLight source
def read_stl(path):
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    hi = next(i for i, r in enumerate(rows) if "INTID" in r and "NBL" in r)
    h = rows[hi]; ix = {k: h.index(k) for k in ["DATE", "Day Type", "TIME", "Intersection Name"] + MOV}
    data, period = {}, ""
    for r in rows[hi + 1:]:
        if len(r) < len(h) or not r[ix["Intersection Name"]]: continue
        period = period or r[ix["DATE"]]
        t = r[ix["TIME"]].strip()
        data.setdefault(r[ix["Intersection Name"]], {}).setdefault(r[ix["Day Type"]], {})[t] = [int(float(r[ix[k]] or 0)) for k in MOV]
    return {"name": "StreetLight TMC 2098249 (S Platte River Dr)", "kind": "streetlight_tmc", "period": period,
            "imported": "2026-11-02", "data": data}


def hour(src, inter, dt, start, n=4):
    by = src["data"][inter][dt]; m = {k: 0 for k in MOV}; t = int(start[:-2]) * 60 + int(start[-2:])
    for i in range(n):
        tt = t + 15 * i; key = f"{tt // 60}{tt % 60:02d}"
        for k, v in zip(MOV, by.get(key, [0] * 12)): m[k] += v
    return m


def build():
    src = read_stl(STL_CSV)
    dt, start = "0: All Days (M-Su)", "1700"
    for nid, t in SC_TMC.items():
        if "source" in t:
            m = hour(src, t["source"]["intersection"], dt, start)
            m.update(t.get("movements", {})); t["movements"] = m
    model = {
        "meta": {"name": "I-25 / Santa Fe Dr volume balance", "description": "Built from AK_Volume Balance.xlsx (Baseline 5PM), CDOT TCDS counts and StreetLight TMC 2098249.", "version": 1},
        "settings": {"baseYear": 2026, "growthPct": 0, "okPct": 5, "warnPct": 10},
        "defaultScenario": "baseline_pm",
        "scenarios": {"baseline_pm": {"name": "Baseline (5 PM)", "dayType": dt, "start": start, "bins": 4, "links": SC_LINKS, "tmc": SC_TMC}},
        "nodes": NODES, "links": LINKS,
        "sources": {"stl_2098249": src},
    }
    ids = [n["id"] for n in NODES]; assert len(ids) == len(set(ids)), "duplicate node id"
    for l in LINKS:
        assert l["from"] in ids and l["to"] in ids, f"bad link {l['id']}"
    return model


def embed(model):
    html = PAGE.read_text(encoding="utf-8")
    blob = json.dumps(model, separators=(",", ":")).replace("</", "<\\/")
    new = re.sub(r'(<script id="embedded-data" type="application/json">).*?(</script>)', lambda m: m.group(1) + blob + m.group(2), html, count=1, flags=re.S)
    PAGE.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    model = build()
    OUT_JSON.write_text(json.dumps(model, indent=1, ensure_ascii=False), encoding="utf-8")
    embed(model)
    print(f"nodes {len(NODES)}, links {len(LINKS)} -> {OUT_JSON.name}; embedded into {PAGE.name}")
