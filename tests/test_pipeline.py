import json

import numpy as np
import pandas as pd
import pytest

from scripts.make_synthetic import make
from src.analysis.evaluation import h1_cross_sensor_test, mark_cross_sensor_matches
from src.api.service import DataStore, Filters, NotFound
from src.clustering.events import summarise_events
from src.clustering.st_dbscan import cluster_detections, st_dbscan_labels
from src.processing.clean import CleaningConfig, clean_detections
from src.processing.schema import SchemaError, parse_datetime, to_unified


@pytest.fixture(scope="module")
def raw():
    return make()


@pytest.fixture(scope="module")
def cleaned(raw):
    v, m = raw
    dv, rv = clean_detections(to_unified(v, "v.csv"))
    dm, _ = clean_detections(to_unified(m, "m.csv"))
    return dv, dm, rv


# ---------- schema & cleaning ----------
def test_sensor_detection_and_confidence_mapping(raw):
    v, m = raw
    uv, um = to_unified(v), to_unified(m)
    assert set(uv["sensor"]) == {"VIIRS"} and set(um["sensor"]) == {"MODIS"}
    assert set(uv["confidence_level"].dropna()) <= {"low", "nominal", "high"}
    assert set(um["confidence_level"]) == {"nominal"}  # synthetic MODIS confidence = 70


def test_acq_time_without_zero_padding():
    t = parse_datetime(pd.Series(["2025-07-01", "2025-07-01"]), pd.Series([5, 1342]))
    assert t.iloc[0].strftime("%H:%M") == "00:05" and t.iloc[1].strftime("%H:%M") == "13:42"


def test_missing_required_column_raises():
    with pytest.raises(SchemaError):
        to_unified(pd.DataFrame({"latitude": [1.0], "longitude": [2.0]}))


def test_cleaning_report_counts(cleaned, raw):
    dv, _, rep = cleaned
    steps = {s["rule"].split(" (")[0]: s["removed"] for s in rep.steps}
    assert steps["impossible coordinates"] == 1
    assert steps["exact duplicates"] == 1
    assert steps["non-vegetation source type"] == 50  # gas flare
    assert steps["low confidence"] == 10
    assert rep.raw_rows == len(raw[0]) and rep.retained_rows == len(dv)
    assert dv["detection_id"].is_unique


def test_empty_input_does_not_crash():
    empty = to_unified(pd.DataFrame(columns=["latitude", "longitude", "acq_date", "acq_time", "bright_ti4"]))
    df, rep = clean_detections(empty)
    assert len(df) == 0 and rep.retained_rows == 0
    assert len(st_dbscan_labels(np.array([]), np.array([]), pd.Series([], dtype="datetime64[ns, UTC]"))) == 0


# ---------- clustering ----------
def test_temporal_constraint_splits_same_place_different_time():
    t = pd.to_datetime(["2025-07-01 08:00", "2025-07-01 20:00", "2025-09-01 08:00", "2025-09-01 20:00"], utc=True)
    lat, lon = np.array([50.0, 50.001, 50.0, 50.001]), np.array([80.0, 80.001, 80.0, 80.001])
    spatial = st_dbscan_labels(lat, lon, t, eps_km=3, eps_days=None)
    st = st_dbscan_labels(lat, lon, t, eps_km=3, eps_days=2)
    assert len(set(spatial)) == 1
    assert len(set(st)) == 2 and -1 not in st


def test_far_points_are_noise():
    t = pd.to_datetime(["2025-07-01"] * 2, utc=True)
    labels = st_dbscan_labels(np.array([45.0, 50.0]), np.array([60.0, 80.0]), t)
    assert list(labels) == [-1, -1]


def test_event_summary(cleaned):
    dv, _, _ = cleaned
    c = cluster_detections(dv, eps_km=3, eps_days=2)
    ev = summarise_events(c)
    assert len(ev) >= 4
    assert ev["n_detections"].sum() == (~c["is_noise"]).sum()
    big = ev.sort_values("n_detections").iloc[-1]
    assert big["priority"] == "high" and big["hull"][0] == big["hull"][-1]
    assert (ev["end_time"] >= ev["start_time"]).all()


# ---------- evaluation ----------
def test_cross_sensor_matching_tolerances():
    tgt = pd.DataFrame({"latitude": [50.0, 50.0], "longitude": [80.0, 80.0],
                        "acq_datetime": pd.to_datetime(["2025-07-01", "2025-07-10"], utc=True)})
    ref = pd.DataFrame({"latitude": [50.01], "longitude": [80.0],
                        "acq_datetime": pd.to_datetime(["2025-07-01 12:00"], utc=True)})
    assert list(mark_cross_sensor_matches(tgt, ref, 3, 1)) == [True, False]


def test_h1_runs_on_synthetic(cleaned):
    dv, dm, _ = cleaned
    res = h1_cross_sensor_test(cluster_detections(dv), dm)
    assert res["event_confirmation_rate"] > res["isolated_confirmation_rate"]
    assert 0 <= res["p_value"] <= 1


# ---------- service layer (what the API returns) ----------
@pytest.fixture(scope="module")
def store(tmp_path_factory, raw):
    from src import pipeline
    from src.core import config

    tmp = tmp_path_factory.mktemp("data")
    v, m = raw
    (tmp / "raw").mkdir()
    v.to_csv(tmp / "raw" / "v.csv", index=False)
    m.to_csv(tmp / "raw" / "m.csv", index=False)
    object.__setattr__(config.settings, "data_dir", tmp)
    pipeline.run("test", [str(tmp / "raw" / "v.csv")], [str(tmp / "raw" / "m.csv")], regions=str(tmp / "none"))
    return DataStore(tmp / "processed")


def test_store_lists_and_filters(store):
    assert store.list_datasets()[0]["dataset"] == "test"
    all_ev = store.events("test", Filters())
    viirs = store.events("test", Filters(sensor="VIIRS"))
    high = store.events("test", Filters(min_priority="high"))
    assert 0 < len(viirs) < len(all_ev) and len(high) <= len(all_ev)
    july = store.detections("test", Filters(start="2025-07-01", end="2025-07-05"))
    assert july["acq_datetime"].max() < pd.Timestamp("2025-07-06", tz="UTC")
    hc = store.detections("test", Filters(min_confidence="high"))
    assert set(hc["confidence_level"]) == {"high"}


def test_store_event_detail_and_stats(store):
    eid = store.events("test", Filters(), sort="-n_detections").iloc[0]["event_id"]
    d = store.event_detail("test", eid)
    assert d["event"]["n_detections"] == len(d["detections"]) and d["event"]["daily"]
    s = store.summary("test", Filters())
    assert s["detected_events"] == len(store.events("test", Filters()))
    assert store.timeseries("test", Filters(), "W")
    assert store.by_region("test", Filters())[0]["region"] == "Unassigned"
    json.dumps(d["event"])  # must be JSON-serialisable
    with pytest.raises(NotFound):
        store.event_detail("test", "nope")
