"""Load NASA FIRMS CSV files (archive or NRT, VIIRS or MODIS) into one common schema.

FIRMS column conventions (see FIRMS attribute documentation):
  VIIRS : bright_ti4, bright_ti5, confidence in {l, n, h} (or low/nominal/high)
  MODIS : brightness, bright_t31, confidence in 0..100 (%)
  Archive / country files additionally carry ``type``:
      0 = presumed vegetation fire, 1 = active volcano,
      2 = other static land source (e.g. gas flares), 3 = offshore
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["latitude", "longitude", "acq_date", "acq_time"]

UNIFIED_COLUMNS = [
    "detection_id",
    "latitude",
    "longitude",
    "acq_datetime",
    "acq_date",
    "sensor",
    "satellite",
    "brightness_k",
    "brightness2_k",
    "frp",
    "scan",
    "track",
    "confidence_raw",
    "confidence_level",
    "daynight",
    "type",
    "source_file",
]

_VIIRS_CONF = {"l": "low", "low": "low", "n": "nominal", "nominal": "nominal", "h": "high", "high": "high"}


class SchemaError(ValueError):
    """Raised when an input file lacks the fields needed for analysis."""


def detect_sensor(df: pd.DataFrame, hint: str | None = None) -> str:
    """Return 'VIIRS' or 'MODIS' based on columns (or the instrument field)."""
    if "instrument" in df.columns and df["instrument"].notna().any():
        value = str(df["instrument"].dropna().iloc[0]).upper()
        if value in {"VIIRS", "MODIS"}:
            return value
    if "bright_ti4" in df.columns:
        return "VIIRS"
    if "brightness" in df.columns:
        return "MODIS"
    if hint:
        return hint.upper()
    raise SchemaError("Cannot detect sensor: neither bright_ti4 (VIIRS) nor brightness (MODIS) present.")


def modis_confidence_level(values: pd.Series) -> pd.Series:
    """FIRMS MODIS classes: low < 30 <= nominal < 80 <= high."""
    num = pd.to_numeric(values, errors="coerce")
    out = pd.Series(pd.NA, index=values.index, dtype="object")
    out[num < 30] = "low"
    out[(num >= 30) & (num < 80)] = "nominal"
    out[num >= 80] = "high"
    return out


def viirs_confidence_level(values: pd.Series) -> pd.Series:
    return values.astype("string").str.strip().str.lower().map(_VIIRS_CONF).astype("object")


def parse_datetime(acq_date: pd.Series, acq_time: pd.Series) -> pd.Series:
    """Combine FIRMS acq_date (YYYY-MM-DD) and acq_time (HHMM, UTC, may lack zero padding)."""
    t = pd.to_numeric(acq_time, errors="coerce")
    hhmm = t.map(lambda v: f"{int(v):04d}" if pd.notna(v) else None)
    combined = acq_date.astype("string").str.strip() + " " + hhmm.astype("string")
    return pd.to_datetime(combined, format="%Y-%m-%d %H%M", errors="coerce", utc=True)


def to_unified(raw: pd.DataFrame, source_file: str = "", sensor_hint: str | None = None) -> pd.DataFrame:
    """Map one raw FIRMS table to the unified schema (no rows are dropped here)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise SchemaError(f"{source_file or 'input'}: missing required columns {missing}")

    sensor = detect_sensor(raw, sensor_hint)
    out = pd.DataFrame(index=raw.index)
    out["latitude"] = pd.to_numeric(raw["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(raw["longitude"], errors="coerce")
    out["acq_datetime"] = parse_datetime(raw["acq_date"], raw["acq_time"])
    out["acq_date"] = out["acq_datetime"].dt.strftime("%Y-%m-%d")
    out["sensor"] = sensor
    out["satellite"] = raw.get("satellite", pd.Series(pd.NA, index=raw.index)).astype("string")

    if sensor == "VIIRS":
        b1, b2 = raw.get("bright_ti4"), raw.get("bright_ti5")
    else:
        b1, b2 = raw.get("brightness"), raw.get("bright_t31")
    out["brightness_k"] = pd.to_numeric(b1, errors="coerce") if b1 is not None else np.nan
    out["brightness2_k"] = pd.to_numeric(b2, errors="coerce") if b2 is not None else np.nan
    for col in ("frp", "scan", "track"):
        out[col] = pd.to_numeric(raw[col], errors="coerce") if col in raw.columns else np.nan

    conf = raw["confidence"] if "confidence" in raw.columns else pd.Series(pd.NA, index=raw.index)
    out["confidence_raw"] = conf.astype("string")
    out["confidence_level"] = (
        viirs_confidence_level(conf) if sensor == "VIIRS" else modis_confidence_level(conf)
    )
    out["daynight"] = raw.get("daynight", pd.Series(pd.NA, index=raw.index)).astype("string")
    out["type"] = (
        pd.to_numeric(raw["type"], errors="coerce").astype("Int64")
        if "type" in raw.columns
        else pd.Series(pd.NA, index=raw.index, dtype="Int64")
    )
    out["source_file"] = source_file
    out["detection_id"] = ""
    return out[UNIFIED_COLUMNS]


def load_firms_csv(path: str | Path, sensor_hint: str | None = None) -> pd.DataFrame:
    path = Path(path)
    raw = pd.read_csv(path, low_memory=False)
    return to_unified(raw, source_file=path.name, sensor_hint=sensor_hint)
