"""HTTP-level tests. Require fastapi + httpx (pip install -r requirements.txt)."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from scripts.make_synthetic import make  # noqa: E402


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from src import pipeline
    from src.api import app as app_module
    from src.api.service import DataStore
    from src.core import config

    tmp = tmp_path_factory.mktemp("apidata")
    (tmp / "raw").mkdir()
    v, m = make()
    v.to_csv(tmp / "raw" / "v.csv", index=False)
    m.to_csv(tmp / "raw" / "m.csv", index=False)
    object.__setattr__(config.settings, "data_dir", tmp)
    pipeline.run("kz_2025", [str(tmp / "raw" / "v.csv")], [str(tmp / "raw" / "m.csv")], regions=str(tmp / "x"))
    app_module.store = DataStore(tmp / "processed")
    return TestClient(app_module.app)


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and "kz_2025" in r.json()["datasets"]


def test_events_geojson_and_detail(client):
    fc = client.get("/api/v1/events", params={"sort": "-n_detections", "geometry": "hull"}).json()
    assert fc["type"] == "FeatureCollection" and fc["features"]
    eid = fc["features"][0]["id"]
    d = client.get(f"/api/v1/events/{eid}").json()
    assert d["event"]["event_id"] == eid and d["detections"]["features"]
    assert client.get("/api/v1/events/NOPE").status_code == 404


def test_filters_and_validation(client):
    assert client.get("/api/v1/events", params={"sensor": "XYZ"}).status_code == 422
    assert client.get("/api/v1/events", params={"bbox": "1,2,3"}).status_code == 422
    r = client.get("/api/v1/detections", params={"min_confidence": "high", "limit": 5}).json()
    assert len(r["features"]) <= 5 and r["total"] >= len(r["features"])


def test_stats_eval_export(client):
    assert client.get("/api/v1/stats/summary").json()["satellite_detections"] > 0
    assert client.get("/api/v1/stats/timeseries", params={"freq": "W"}).json()
    assert client.get("/api/v1/stats/regions").status_code == 200
    assert "h1_cross_sensor" in client.get("/api/v1/evaluation").json()["evaluation"]
    csv = client.get("/api/v1/export/events.csv")
    assert csv.status_code == 200 and csv.text.startswith("event_id")


def test_refresh_without_key(client, monkeypatch):
    from src.core import config

    object.__setattr__(config.settings, "firms_map_key", None)
    assert client.post("/api/v1/refresh").status_code == 503
