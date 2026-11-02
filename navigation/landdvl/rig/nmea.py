"""NMEA parsing for the GNSS receiver (GGA for position and fix type, GST for accuracy).

The simpleRTK3B (Unicore UM980) and u-blox receivers both output standard NMEA 0183.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS = 6_378_137.0  # m, WGS-84 equatorial radius

# GGA fix quality -> log quality. 4 = RTK fixed, 5 = RTK float; everything else counts as
# "none" because only RTK is accurate enough to judge the filter against.
QUALITY = {4: "fix", 5: "float"}
# Accuracy to assume when no GST sentence is available (m).
DEFAULT_SIGMA = {"fix": 0.02, "float": 0.30, "none": 3.0}


def checksum_ok(sentence: str) -> bool:
    if not sentence.startswith("$") or "*" not in sentence:
        return False
    body, _, given = sentence[1:].partition("*")
    calc = 0
    for ch in body:
        calc ^= ord(ch)
    try:
        return calc == int(given[:2], 16)
    except ValueError:
        return False


def _degrees(value: str, hemisphere: str) -> float:
    """ddmm.mmmm (or dddmm.mmmm) to signed decimal degrees."""
    dot = value.index(".")
    deg = float(value[: dot - 2])
    minutes = float(value[dot - 2 :])
    sign = -1.0 if hemisphere in ("S", "W") else 1.0
    return sign * (deg + minutes / 60.0)


def utc_seconds(utc: str) -> float | None:
    """hhmmss.ss to seconds of the day."""
    try:
        return int(utc[0:2]) * 3600 + int(utc[2:4]) * 60 + float(utc[4:])
    except (ValueError, IndexError):
        return None


@dataclass
class GGA:
    utc: str
    lat: float
    lon: float
    quality: str  # fix / float / none
    raw_quality: int
    satellites: int
    hdop: float
    altitude: float


@dataclass
class GST:
    utc: str
    sigma_lat: float
    sigma_lon: float

    @property
    def sigma(self) -> float:
        """One horizontal standard deviation (RMS of north and east)."""
        return math.sqrt((self.sigma_lat**2 + self.sigma_lon**2) / 2.0)


def parse(sentence: str) -> GGA | GST | None:
    """Parse one NMEA sentence. Returns None for other sentences, bad checksums or no data."""
    sentence = sentence.strip()
    if not checksum_ok(sentence):
        return None
    fields = sentence[1:].split("*")[0].split(",")
    kind = fields[0][2:]  # GPGGA, GNGGA, ... -> GGA
    try:
        if kind == "GGA" and len(fields) >= 10 and fields[2] and fields[4]:
            raw = int(fields[6] or 0)
            return GGA(
                utc=fields[1],
                lat=_degrees(fields[2], fields[3]),
                lon=_degrees(fields[4], fields[5]),
                quality=QUALITY.get(raw, "none"),
                raw_quality=raw,
                satellites=int(fields[7] or 0),
                hdop=float(fields[8] or "nan"),
                altitude=float(fields[9] or "nan"),
            )
        if kind == "GST" and len(fields) >= 8 and fields[6] and fields[7]:
            return GST(utc=fields[1], sigma_lat=float(fields[6]), sigma_lon=float(fields[7]))
    except ValueError:
        return None
    return None


class LocalFrame:
    """Latitude/longitude to local east/north metres around the first position.

    A flat-earth approximation: the error is far below a centimetre over a garden (< 1 km).
    """

    def __init__(self, lat0: float, lon0: float):
        self.lat0 = lat0
        self.lon0 = lon0
        self._cos = math.cos(math.radians(lat0))

    def to_local(self, lat: float, lon: float) -> tuple[float, float]:
        east = math.radians(lon - self.lon0) * EARTH_RADIUS * self._cos
        north = math.radians(lat - self.lat0) * EARTH_RADIUS
        return east, north

    def to_latlon(self, east: float, north: float) -> tuple[float, float]:
        lat = self.lat0 + math.degrees(north / EARTH_RADIUS)
        lon = self.lon0 + math.degrees(east / (EARTH_RADIUS * self._cos))
        return lat, lon


def make_sentence(body: str) -> str:
    """Add $ and checksum, for tests and the loopback simulator."""
    calc = 0
    for ch in body:
        calc ^= ord(ch)
    return f"${body}*{calc:02X}"


def format_gga(utc: str, lat: float, lon: float, raw_quality: int, sats: int = 20) -> str:
    def dm(value: float, width: int) -> str:
        a = abs(value)
        deg = int(a)
        return f"{deg:0{width}d}{(a - deg) * 60:011.8f}"

    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    body = (
        f"GNGGA,{utc},{dm(lat, 2)},{ns},{dm(lon, 3)},{ew},{raw_quality},{sats},0.6,30.0,M,40.0,M,,"
    )
    return make_sentence(body)
