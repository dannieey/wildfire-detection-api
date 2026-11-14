"""Quantitative evaluation used to test the paper's hypotheses.

H1  Cross-sensor confirmation: VIIRS candidate events (clusters) are confirmed by an
    independent sensor (MODIS, different satellites and algorithm) more often than
    isolated VIIRS detections.  Test: chi-square test of independence on a 2x2
    table (+ odds ratio, Cramer's V); size-bin trend as a secondary analysis.
H2  Temporal constraint: spatiotemporal DBSCAN yields temporally more coherent
    events than spatial-only DBSCAN (shorter durations, fewer events spanning
    > 7 days).  Test: Mann-Whitney U on event durations (one-sided).
Plus: data-reduction ratio and a parameter-sensitivity grid.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.neighbors import BallTree

from src.clustering.events import summarise_events
from src.clustering.st_dbscan import EARTH_RADIUS_KM, _to_days, cluster_detections


def mark_cross_sensor_matches(
    target: pd.DataFrame, reference: pd.DataFrame, match_km: float = 3.0, match_days: float = 1.0
) -> pd.Series:
    """True where a target detection has >=1 reference detection within match_km and +-match_days."""
    if target.empty or reference.empty:
        return pd.Series(False, index=target.index)
    tree = BallTree(np.radians(reference[["latitude", "longitude"]].to_numpy()), metric="haversine")
    ind = tree.query_radius(np.radians(target[["latitude", "longitude"]].to_numpy()), r=match_km / EARTH_RADIUS_KM)
    t_tgt, t_ref = _to_days(target["acq_datetime"]), _to_days(reference["acq_datetime"])
    hit = np.fromiter(
        (len(nb) > 0 and bool((np.abs(t_ref[nb] - t_tgt[i]) <= match_days).any()) for i, nb in enumerate(ind)),
        dtype=bool, count=len(target),
    )
    return pd.Series(hit, index=target.index)


def h1_cross_sensor_test(clustered_viirs: pd.DataFrame, modis: pd.DataFrame, match_km=3.0, match_days=1.0) -> dict:
    d = clustered_viirs.copy()
    d["confirmed"] = mark_cross_sensor_matches(d, modis, match_km, match_days)
    ev = d[~d["is_noise"]].groupby("event_id").agg(confirmed=("confirmed", "any"), size=("confirmed", "size"))
    iso = d[d["is_noise"]]
    table = np.array(
        [[int(ev["confirmed"].sum()), int((~ev["confirmed"]).sum())],
         [int(iso["confirmed"].sum()), int((~iso["confirmed"]).sum())]]
    )
    result = {
        "hypothesis": "H1: clustered events are confirmed by MODIS more often than isolated VIIRS detections",
        "match_km": match_km, "match_days": match_days,
        "contingency_table": {"rows": ["clustered events", "isolated detections"],
                              "cols": ["confirmed", "not confirmed"], "values": table.tolist()},
        "point_level_confirmation_rate": round(float(d["confirmed"].mean()), 4) if len(d) else None,
    }
    if (table.sum(axis=1) == 0).any():
        result["note"] = "Insufficient data for test (one group empty)."
        return result
    rate_ev, rate_iso = table[:, 0] / table.sum(axis=1)
    chi2, p, dof, expected = stats.chi2_contingency(table, correction=True)
    n = table.sum()
    a, b, c, dd = (table + 0.5).ravel()  # Haldane correction for odds ratio
    result.update({
        "event_confirmation_rate": round(float(rate_ev), 4),
        "isolated_confirmation_rate": round(float(rate_iso), 4),
        "chi2": round(float(chi2), 3), "dof": int(dof), "p_value": float(p),
        "cramers_v": round(float(np.sqrt(chi2 / n)), 4),
        "odds_ratio": round(float((a * dd) / (b * c)), 3),
        "min_expected_count": round(float(expected.min()), 2),
        "reject_h0_at_0.05": bool(p < 0.05 and rate_ev > rate_iso),
    })
    if expected.min() < 5:
        result["fisher_exact_p"] = float(stats.fisher_exact(table, alternative="greater")[1])
    # Secondary: confirmation rate by event size (isolated points = size 1)
    sizes = pd.concat([ev["size"], pd.Series(1, index=iso.index)])
    conf = pd.concat([ev["confirmed"], iso["confirmed"]])
    bins = pd.cut(sizes, [0, 1, 4, 19, np.inf], labels=["1 (isolated)", "2-4", "5-19", "20+"])
    by_bin = pd.crosstab(bins, conf).reindex(columns=[True, False], fill_value=0)
    by_bin = by_bin[by_bin.sum(axis=1) > 0]
    result["by_size_bin"] = [
        {"size_bin": str(k), "n": int(r.sum()), "confirmation_rate": round(float(r[True] / r.sum()), 4)}
        for k, r in by_bin.iterrows()
    ]
    if len(by_bin) >= 2:
        chi2_b, p_b, dof_b, _ = stats.chi2_contingency(by_bin.to_numpy())
        result["size_bin_chi2"] = {"chi2": round(float(chi2_b), 3), "dof": int(dof_b), "p_value": float(p_b)}
    return result


def describe_clustering(df_clustered: pd.DataFrame, events: pd.DataFrame) -> dict:
    n = len(df_clustered)
    n_noise = int(df_clustered["is_noise"].sum())
    dur = events["duration_hours"] if len(events) else pd.Series(dtype=float)
    return {
        "n_detections": n,
        "n_events": int(len(events)),
        "n_isolated": n_noise,
        "noise_pct": round(100 * n_noise / n, 2) if n else 0.0,
        "review_items": int(len(events) + n_noise),
        "reduction_pct": round(100 * (1 - (len(events) + n_noise) / n), 2) if n else 0.0,
        "median_detections_per_event": float(events["n_detections"].median()) if len(events) else 0.0,
        "median_duration_hours": float(dur.median()) if len(dur) else 0.0,
        "p90_duration_hours": float(dur.quantile(0.9)) if len(dur) else 0.0,
        "share_events_over_7_days": round(float((dur > 7 * 24).mean()), 4) if len(dur) else 0.0,
        "n_high_priority": int((events["priority"] == "high").sum()) if len(events) else 0,
        "n_persistent_hotspots": int(events["persistent_hotspot"].sum()) if len(events) else 0,
    }


def h2_temporal_vs_spatial(df: pd.DataFrame, eps_km=3.0, eps_days=2.0, min_samples=2) -> dict:
    sp = cluster_detections(df, eps_km=eps_km, eps_days=None, min_samples=min_samples)
    st = cluster_detections(df, eps_km=eps_km, eps_days=eps_days, min_samples=min_samples)
    ev_sp, ev_st = summarise_events(sp), summarise_events(st)
    out = {
        "hypothesis": "H2: the temporal constraint produces shorter, temporally coherent events",
        "spatial_only": describe_clustering(sp, ev_sp),
        "spatiotemporal": describe_clustering(st, ev_st),
        "params": {"eps_km": eps_km, "eps_days": eps_days, "min_samples": min_samples},
    }
    if len(ev_sp) and len(ev_st):
        u, p = stats.mannwhitneyu(ev_st["duration_hours"], ev_sp["duration_hours"], alternative="less")
        out.update({"mann_whitney_u": float(u), "p_value": float(p), "reject_h0_at_0.05": bool(p < 0.05)})
    return out


def sensitivity_grid(df: pd.DataFrame, eps_km_values=(1, 2, 3, 5), eps_days_values=(1, 2, 3), min_samples=2) -> list[dict]:
    rows = []
    for ek in eps_km_values:
        for ed in eps_days_values:
            c = cluster_detections(df, eps_km=ek, eps_days=ed, min_samples=min_samples)
            e = summarise_events(c)
            rows.append({"eps_km": ek, "eps_days": ed, **describe_clustering(c, e)})
    return rows
