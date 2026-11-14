"""Generate publication figures (PNG, 300 dpi) and result tables for the paper.

Usage: python scripts/make_figures.py [dataset_name]
Reads  data/processed/<dataset>/ and data/reference/kaz_adm1.geojson
Writes docs/figures/*.png and docs/results/*.md|*.csv
All labels are in English (course requirement).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DS = sys.argv[1] if len(sys.argv) > 1 else "kz_2025"
SRC = ROOT / "data" / "processed" / DS
FIG = ROOT / "docs" / "figures"
TAB = ROOT / "docs" / "results"

# Validated categorical slots (light mode) + text / grid tokens
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#ffffff"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.dpi": 300, "savefig.bbox": "tight", "legend.frameon": False,
})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    print("figure", name)


def bar_labels(ax, bars, fmt="{:,.0f}", inside=False):
    for b in bars:
        h = b.get_height()
        ax.annotate(fmt.format(h), (b.get_x() + b.get_width() / 2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color=INK2)


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)


def main():
    meta = json.loads((SRC / "meta.json").read_text())
    ev_json = json.loads((SRC / "evaluation.json").read_text())
    det = pd.read_csv(SRC / "detections.csv", low_memory=False, dtype={"confidence_raw": str})
    ev = pd.read_csv(SRC / "events.csv", low_memory=False)
    det["month"] = pd.to_datetime(det["acq_date"]).dt.month
    TAB.mkdir(parents=True, exist_ok=True)
    tables = []

    # ---- Table 1 + Fig 1: data cleaning flow -------------------------------------------
    rows = []
    for sensor, q in meta["quality"].items():
        rows.append({"Sensor": sensor, "Step": "Raw records", "Removed": "-", "Remaining": q["raw_rows"]})
        for s in q["steps"]:
            if s["removed"]:
                rows.append({"Sensor": sensor, "Step": s["rule"].capitalize(), "Removed": s["removed"],
                             "Remaining": s["remaining"]})
        if q.get("outside_country_removed_total"):
            rows.append({"Sensor": sensor, "Step": "Outside national border (both sensors)",
                         "Removed": q["outside_country_removed_total"], "Remaining": "-"})
    t1 = pd.DataFrame(rows)
    tables.append(("Table 1. Data-cleaning steps and record counts (NASA FIRMS, Kazakhstan, 2025)", t1))

    q = meta["quality"]["VIIRS"]
    labels = ["Raw records"] + [s["rule"].split(" (")[0].capitalize() for s in q["steps"] if s["removed"]]
    values = [q["raw_rows"]] + [s["remaining"] for s in q["steps"] if s["removed"]]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    y = np.arange(len(labels))[::-1]
    bars = ax.barh(y, values, color=BLUE, height=0.55)
    ax.set_yticks(y, [f"{l}" if i == 0 else f"After removing: {l.lower()}" for i, l in enumerate(labels)])
    for b, v in zip(bars, values):
        ax.annotate(f"{v:,}", (v, b.get_y() + b.get_height() / 2), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.set_xlabel("VIIRS records remaining")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_title("Figure 1. VIIRS data-cleaning flow", loc="left")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(values) * 1.15)
    save(fig, "fig1_cleaning_flow")

    # ---- Fig 2: monthly detections by sensor -------------------------------------------
    m = det.groupby(["month", "sensor"]).size().unstack(fill_value=0).reindex(range(1, 13), fill_value=0)
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    x = np.arange(12)
    w = 0.38
    b1 = ax.bar(x - w / 2 - 0.01, m.get("VIIRS", 0), w, color=BLUE, label="VIIRS (375 m)")
    b2 = ax.bar(x + w / 2 + 0.01, m.get("MODIS", 0), w, color=ORANGE, label="MODIS (1 km)")
    ax.set_xticks(x, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Cleaned detections")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    peak = int(m["VIIRS"].idxmax())
    ax.annotate(f"{m['VIIRS'].max():,}", (peak - 1 - w / 2, m["VIIRS"].max()), xytext=(0, 3),
                textcoords="offset points", ha="center", fontsize=8, color=INK2)
    ax.legend(loc="upper right")
    ax.set_title("Figure 2. Monthly thermal-anomaly detections, Kazakhstan 2025", loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig2_monthly_detections")
    t_month = m.reset_index().rename(columns={"month": "Month"})
    t_month.to_csv(TAB / "monthly_detections.csv", index=False)

    # ---- Fig 3 + Table: regions ---------------------------------------------------------
    rd = det.groupby("region").size().rename("Detections")
    re_ = ev.groupby("region").agg(Events=("event_id", "size"),
                                  **{"High-priority events": ("priority", lambda s: int((s == "high").sum()))})
    reg = pd.concat([rd, re_], axis=1).fillna(0).astype(int).sort_values("Detections")
    fig, ax = plt.subplots(figsize=(7, 4.6))
    bars = ax.barh(reg.index, reg["Detections"], color=BLUE, height=0.6)
    for b, v in zip(bars, reg["Detections"]):
        ax.annotate(f"{v:,}", (v, b.get_y() + b.get_height() / 2), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK2)
    ax.set_xlabel("Cleaned detections (VIIRS + MODIS)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_xlim(0, reg["Detections"].max() * 1.15)
    ax.set_title("Figure 3. Detections by region (pre-2018 ADM1 boundaries)", loc="left")
    ax.grid(axis="y", visible=False)
    save(fig, "fig3_regions")
    t_reg = reg.sort_values("Detections", ascending=False).reset_index().rename(columns={"region": "Region"})
    tables.append(("Table 2. Detections and candidate events by region", t_reg))

    # ---- Fig 4: map of events -----------------------------------------------------------
    gpath = ROOT / "data" / "reference" / "kaz_adm1.geojson"
    fig, ax = plt.subplots(figsize=(8, 5))
    if gpath.exists():
        gj = json.loads(gpath.read_text())
        for f in gj["features"]:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for p in polys:
                r = np.asarray(p[0])
                ax.fill(r[:, 0], r[:, 1], color="#f3f2ee", zorder=0)
                ax.plot(r[:, 0], r[:, 1], color=MUTED, lw=0.5, zorder=1)
    ev["season"] = pd.to_datetime(ev["start_time"], utc=True, format="ISO8601").dt.month.map(
        lambda mm: "Spring (Mar-May)" if 3 <= mm <= 5 else "Summer (Jun-Aug)" if 6 <= mm <= 8
        else "Autumn (Sep-Nov)" if 9 <= mm <= 11 else None)
    v = ev[(ev["sensor"] == "VIIRS") & ev["season"].notna()]
    for season, color in [("Spring (Mar-May)", BLUE), ("Summer (Jun-Aug)", ORANGE), ("Autumn (Sep-Nov)", AQUA)]:
        s = v[v["season"] == season]
        ax.scatter(s["centroid_lon"], s["centroid_lat"], s=np.clip(np.sqrt(s["n_detections"]) * 4, 6, 120),
                   color=color, alpha=0.55, edgecolors=SURFACE, linewidths=0.4, label=f"{season}: {len(s):,}",
                   zorder=2)
    ax.set_aspect(1 / np.cos(np.radians(48)))
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.legend(loc="lower left", title="VIIRS candidate events (size = detections)", title_fontsize=8, fontsize=8)
    ax.set_title("Figure 4. Spatial distribution of candidate wildfire events, 2025", loc="left")
    ax.grid(False)
    save(fig, "fig4_event_map")

    # ---- Fig 5 + Table: H1 --------------------------------------------------------------
    h1 = ev_json["h1_cross_sensor"]
    sb = pd.DataFrame(h1["by_size_bin"])
    fig, ax = plt.subplots(figsize=(6, 3.4))
    bars = ax.bar(sb["size_bin"], sb["confirmation_rate"] * 100, color=BLUE, width=0.6)
    for b, n, r in zip(bars, sb["n"], sb["confirmation_rate"]):
        ax.annotate(f"{r*100:.1f}%\n(n = {n:,})", (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_ylim(0, 100)
    ax.set_xlabel("VIIRS item size (detections per candidate event)")
    ax.set_ylabel("Confirmed by MODIS (%)")
    ax.set_title("Figure 5. Cross-sensor confirmation by event size (H1)", loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig5_h1_confirmation")
    ct = h1["contingency_table"]["values"]
    t_h1 = pd.DataFrame({
        "Group": ["Clustered events", "Isolated detections"],
        "Confirmed by MODIS": [ct[0][0], ct[1][0]], "Not confirmed": [ct[0][1], ct[1][1]],
        "Confirmation rate": [f"{h1['event_confirmation_rate']*100:.1f}%", f"{h1['isolated_confirmation_rate']*100:.1f}%"],
    })
    tables.append((
        f"Table 3. H1 test: chi-square = {h1['chi2']:.1f}, df = {h1['dof']}, p < 0.001, odds ratio = "
        f"{h1['odds_ratio']:.2f}, Cramer's V = {h1['cramers_v']:.2f} (match: {h1['match_km']:g} km, "
        f"+/-{h1['match_days']:g} day)", t_h1))

    # ---- Fig 6 + Table: H2 --------------------------------------------------------------
    h2 = ev_json["h2_temporal_vs_spatial"]
    sp, st = h2["spatial_only"], h2["spatiotemporal"]
    metrics = [("Candidate events", "n_events", "{:,}"), ("Isolated detections", "n_isolated", "{:,}"),
               ("Items to review", "review_items", "{:,}"), ("Reduction vs raw points", "reduction_pct", "{:.1f}%"),
               ("Median duration (h)", "median_duration_hours", "{:.2f}"),
               ("90th percentile duration (h)", "p90_duration_hours", "{:,.1f}"),
               ("Events longer than 7 days", "share_events_over_7_days", None),
               ("Persistent-hotspot events", "n_persistent_hotspots", "{:,}")]
    rows = []
    for name, k, fmt in metrics:
        f = (lambda v: f"{v*100:.1f}%") if fmt is None else fmt.format
        rows.append({"Metric": name, "Spatial-only DBSCAN": f(sp[k]), "Spatiotemporal DBSCAN": f(st[k])})
    tables.append((f"Table 4. H2 comparison (eps = {h2['params']['eps_km']:g} km, "
                   f"{h2['params']['eps_days']:g} days, min_samples = {h2['params']['min_samples']}); "
                   f"one-sided Mann-Whitney U = {h2['mann_whitney_u']:,.0f}, p < 0.001", pd.DataFrame(rows)))

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    vals = [sp["share_events_over_7_days"] * 100, st["share_events_over_7_days"] * 100]
    bars = ax.bar(["Spatial-only", "Spatiotemporal"], vals, color=[ORANGE, BLUE], width=0.5)
    bar_labels(ax, bars, "{:.1f}%")
    ax.set_ylabel("Events spanning > 7 days (%)")
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title("Figure 6. Temporal over-merging of events (H2)", loc="left")
    ax.grid(axis="x", visible=False)
    save(fig, "fig6_h2_overmerging")

    # ---- Fig 7 + Table: sensitivity -----------------------------------------------------
    sens = pd.DataFrame(ev_json.get("sensitivity_viirs", []))
    if len(sens):
        piv = sens.pivot(index="eps_days", columns="eps_km", values="reduction_pct")
        fig, ax = plt.subplots(figsize=(5.5, 2.8))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", SEQ)
        im = ax.imshow(piv.values, cmap=cmap, vmin=piv.values.min() - 3, vmax=piv.values.max(), aspect="auto")
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                val = piv.values[i, j]
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center", fontsize=9,
                        color="#ffffff" if val > np.median(piv.values) else INK)
        ax.set_xticks(range(piv.shape[1]), [f"{c:g} km" for c in piv.columns])
        ax.set_yticks(range(piv.shape[0]), [f"{r:g} day{'s' if r > 1 else ''}" for r in piv.index])
        ax.set_xlabel("Spatial threshold (eps_km)")
        ax.set_ylabel("Temporal threshold")
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title("Figure 7. Review-load reduction across parameters", loc="left")
        save(fig, "fig7_sensitivity")
        t_s = sens[["eps_km", "eps_days", "n_events", "n_isolated", "noise_pct", "reduction_pct",
                    "share_events_over_7_days"]].copy()
        t_s["share_events_over_7_days"] = (t_s["share_events_over_7_days"] * 100).round(2)
        t_s.columns = ["eps (km)", "eps (days)", "Events", "Isolated", "Noise (%)", "Reduction (%)",
                       "Events > 7 days (%)"]
        tables.append(("Table 5. Parameter sensitivity (VIIRS)", t_s))

    # ---- write tables -------------------------------------------------------------------
    md = ["# Results tables (auto-generated by scripts/make_figures.py)\n",
          f"Dataset: `{DS}`, period {meta['period_start'][:10]} to {meta['period_end'][:10]}, "
          f"{meta['n_detections']:,} cleaned detections, {meta['n_events']:,} candidate events.\n"]
    for title, df in tables:
        md += [f"\n**{title}**\n", md_table(df), ""]
        df.to_csv(TAB / (title.split(".")[0].lower().replace(" ", "_") + ".csv"), index=False)
    (TAB / "results_tables.md").write_text("\n".join(md), encoding="utf-8")
    print("tables written to", TAB)


if __name__ == "__main__":
    main()
