"""NASA FIRMS Area API client (near-real-time data).

URL: {base}/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{DAY_RANGE}[/{YYYY-MM-DD}]
DAY_RANGE is 1..5. A free MAP_KEY is requested at
https://firms.modaps.eosdis.nasa.gov/api/map_key/ and stored in .env as FIRMS_MAP_KEY.
"""
from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from src.core.config import settings

log = logging.getLogger(__name__)

NRT_SOURCES = ("VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT", "VIIRS_SNPP_NRT", "MODIS_NRT")


class FirmsError(RuntimeError):
    pass


def _redact(text: str, key: str | None) -> str:
    return text.replace(key, "***MAP_KEY***") if key else text


def fetch_area(
    source: str,
    bbox: tuple[float, float, float, float] | None = None,
    day_range: int = 2,
    date: str | None = None,
    map_key: str | None = None,
    retries: int = 2,
    timeout: float = 60,
) -> pd.DataFrame:
    key = map_key or settings.firms_map_key
    if not key:
        raise FirmsError("FIRMS_MAP_KEY is not set (add it to .env).")
    if not 1 <= day_range <= 5:
        raise ValueError("FIRMS Area API accepts day_range 1..5")
    w, s, e, n = bbox or settings.kz_bbox
    url = f"{settings.firms_base_url}/api/area/csv/{key}/{source}/{w},{s},{e},{n}/{day_range}"
    if date:
        url += f"/{date}"

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code != 200:
                raise FirmsError(f"HTTP {r.status_code}: {_redact(r.text[:200], key)}")
            text = r.text.strip()
            if not text or not text.lower().startswith("latitude"):
                raise FirmsError(f"Unexpected response: {_redact(text[:200], key)}")
            df = pd.read_csv(io.StringIO(text))
            log.info("FIRMS %s: %d rows", source, len(df))
            return df
        except (requests.RequestException, FirmsError) as err:  # retry with backoff
            last_err = err
            log.warning("FIRMS request failed (%s), attempt %d", _redact(str(err), key), attempt + 1)
            time.sleep(2 ** attempt)
    raise FirmsError(_redact(str(last_err), key))


def download_nrt(out_dir: Path, day_range: int = 3, sources=NRT_SOURCES) -> list[Path]:
    """Download each NRT source to out_dir/nrt_<source>.csv. Failed sources are skipped and logged."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for src in sources:
        try:
            df = fetch_area(src, day_range=day_range)
        except FirmsError as err:
            log.error("Skipping %s: %s", src, err)
            continue
        p = out_dir / f"nrt_{src.lower()}.csv"
        df.to_csv(p, index=False)
        paths.append(p)
    return paths
