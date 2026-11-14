"""Central configuration. Values come from environment variables / .env.

Secrets (FIRMS_MAP_KEY) are never hard-coded and must not be committed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional at runtime
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT_DIR = Path(__file__).resolve().parents[2]


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
    firms_map_key: str | None = os.getenv("FIRMS_MAP_KEY") or None
    firms_base_url: str = os.getenv("FIRMS_BASE_URL", "https://firms.modaps.eosdis.nasa.gov")
    # Kazakhstan bounding box: west, south, east, north
    kz_bbox: tuple[float, float, float, float] = (46.4, 40.5, 87.4, 55.5)

    # Clustering defaults (documented in the paper's Methods section)
    eps_km: float = _env_float("EPS_KM", 3.0)
    eps_days: float = _env_float("EPS_DAYS", 2.0)
    min_samples: int = _env_int("MIN_SAMPLES", 2)

    # Cross-sensor validation tolerance
    match_km: float = _env_float("MATCH_KM", 3.0)
    match_days: float = _env_float("MATCH_DAYS", 1.0)

    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    )

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def reference_dir(self) -> Path:
        return self.data_dir / "reference"


settings = Settings()
